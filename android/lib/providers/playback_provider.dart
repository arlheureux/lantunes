import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';
import '../api/client.dart';
import '../api/websocket.dart';
import '../models/playback_state.dart';
import '../models/track.dart';

class PlaybackProvider extends ChangeNotifier {
  final AudioPlayer _audioPlayer = AudioPlayer();
  PlaybackState _state = PlaybackState();
  List<Device> _devices = [];
  String? _selectedPlayerId;
  String _deviceId = 'android_${DateTime.now().millisecondsSinceEpoch}';
  String _deviceName = 'Android Device';
  StreamSubscription? _wsSubscription;
  Timer? _positionTimer;

  PlaybackState get state => _state;
  List<Device> get devices => _devices;
  String? get selectedPlayerId => _selectedPlayerId;
  String get deviceId => _deviceId;
  bool get isPlayer => _selectedPlayerId == _deviceId || (_selectedPlayerId == null && _devices.length <= 1);

  AudioPlayer get audioPlayer => _audioPlayer;

  Future<void> init(String serverUrl) async {
    ApiClient.setBaseUrl(serverUrl);
    
    // Connect WebSocket
    await WebSocketHandler.connect(serverUrl);
    
    // Register this device
    WebSocketHandler.register(_deviceId, _deviceName);
    
    // Listen to WebSocket messages
    _wsSubscription = WebSocketHandler.messages.listen(_handleWebSocketMessage);
    
    // Fetch initial state
    await refreshState();
  }

  void _handleWebSocketMessage(Map<String, dynamic> msg) {
    final event = msg['event'];
    final data = msg['data'] ?? {};

    switch (event) {
      case 'playback_state':
        final newState = PlaybackState.fromJson(data);
        _state = newState;
        
        // If this device is the player and has stream URL, play it
        if (isPlayer && newState.streamUrl != null && newState.isPlaying) {
          _playAudio(newState.streamUrl!);
        }
        break;
      case 'devices':
        _devices = (data['devices'] as List).map((d) => Device.fromJson(d)).toList();
        final player = _devices.firstWhere(
          (d) => d.isPlayer,
          orElse: () => _devices.isNotEmpty ? _devices.first : Device(id: '', name: '', isPlayer: false),
        );
        _selectedPlayerId = player.id;
        break;
      case 'queue_updated':
        _state = _state.copyWith(queue: List<int>.from(data['queue'] ?? []));
        break;
    }
    notifyListeners();
  }

  Future<void> refreshState() async {
    final state = await ApiClient.getPlaybackState(player: _selectedPlayerId);
    if (state != null) {
      _state = PlaybackState.fromJson(state);
      
      // If this device is player, start playing
      if (isPlayer && _state.streamUrl != null && _state.isPlaying) {
        await _playAudio(_state.streamUrl!);
      }
    }
    notifyListeners();
  }

  Future<void> _playAudio(String url) async {
    try {
      if (_audioPlayer.audioSource?.toString().contains(url) != true) {
        await _audioPlayer.setUrl(url);
      }
      if (_state.isPlaying) {
        await _audioPlayer.play();
      }
    } catch (e) {
      print('Error playing audio: $e');
    }
  }

  Future<void> playTrack(Track track) async {
    await ApiClient.playTrack(trackId: track.id, player: _selectedPlayerId);
  }

  Future<void> play() async {
    await ApiClient.playTrack(player: _selectedPlayerId);
  }

  Future<void> pause() async {
    await ApiClient.pause(player: _selectedPlayerId);
    await _audioPlayer.pause();
  }

  Future<void> next() async {
    await ApiClient.next(player: _selectedPlayerId);
  }

  Future<void> previous() async {
    await ApiClient.previous(player: _selectedPlayerId);
  }

  Future<void> seek(int position) async {
    await ApiClient.seek(position, player: _selectedPlayerId);
    await _audioPlayer.seek(Duration(seconds: position));
  }

  Future<void> setVolume(double volume) async {
    await ApiClient.setVolume(volume, player: _selectedPlayerId);
    await _audioPlayer.setVolume(volume);
  }

  Future<void> toggleShuffle() async {
    await ApiClient.toggleShuffle(player: _selectedPlayerId);
  }

  Future<void> selectPlayer(String deviceId) async {
    _selectedPlayerId = deviceId;
    WebSocketHandler.setPlayer(deviceId);
    await refreshState();
    notifyListeners();
  }

  void updateDeviceName(String name) {
    _deviceName = name;
    WebSocketHandler.register(_deviceId, name);
  }

  @override
  void dispose() {
    _wsSubscription?.cancel();
    _positionTimer?.cancel();
    _audioPlayer.dispose();
    WebSocketHandler.disconnect();
    super.dispose();
  }
}