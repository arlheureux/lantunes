import 'track.dart';

class PlaybackState {
  final Track? track;
  final int position;
  final bool isPlaying;
  final double volume;
  final List<int> queue;
  final int queueIndex;
  final bool shuffleMode;
  final String? playerDeviceId;
  final String? streamUrl;

  PlaybackState({
    this.track,
    this.position = 0,
    this.isPlaying = false,
    this.volume = 1.0,
    this.queue = const [],
    this.queueIndex = 0,
    this.shuffleMode = false,
    this.playerDeviceId,
    this.streamUrl,
  });

  factory PlaybackState.fromJson(Map<String, dynamic> json) {
    return PlaybackState(
      track: json['track'] != null ? Track.fromJson(json['track']) : null,
      position: json['position'] ?? 0,
      isPlaying: json['is_playing'] ?? false,
      volume: (json['volume'] ?? 1.0).toDouble(),
      queue: List<int>.from(json['queue'] ?? []),
      queueIndex: json['queue_index'] ?? 0,
      shuffleMode: json['shuffle_mode'] ?? false,
      playerDeviceId: json['player_device_id'],
      streamUrl: json['track']?['stream_url'],
    );
  }

  PlaybackState copyWith({
    Track? track,
    int? position,
    bool? isPlaying,
    double? volume,
    List<int>? queue,
    int? queueIndex,
    bool? shuffleMode,
    String? playerDeviceId,
    String? streamUrl,
  }) {
    return PlaybackState(
      track: track ?? this.track,
      position: position ?? this.position,
      isPlaying: isPlaying ?? this.isPlaying,
      volume: volume ?? this.volume,
      queue: queue ?? this.queue,
      queueIndex: queueIndex ?? this.queueIndex,
      shuffleMode: shuffleMode ?? this.shuffleMode,
      playerDeviceId: playerDeviceId ?? this.playerDeviceId,
      streamUrl: streamUrl ?? this.streamUrl,
    );
  }
}

class Device {
  final String id;
  final String name;
  final bool isPlayer;

  Device({
    required this.id,
    required this.name,
    required this.isPlayer,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id'] ?? '',
      name: json['name'] ?? 'Unknown',
      isPlayer: json['is_player'] ?? false,
    );
  }
}