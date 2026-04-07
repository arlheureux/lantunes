import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketHandler {
  static WebSocketChannel? _channel;
  static String? _serverUrl;
  static final _controller = StreamController<Map<String, dynamic>>.broadcast();

  static Stream<Map<String, dynamic>> get messages => _controller.stream;

  static Future<void> connect(String serverUrl) async {
    _serverUrl = serverUrl.endsWith('/') ? serverUrl.substring(0, serverUrl.length - 1) : serverUrl;
    final wsUrl = _serverUrl!.replaceFirst('http', 'ws') + '/ws';

    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _channel!.stream.listen(
        (data) {
          try {
            final msg = json.decode(data as String);
            _controller.add(msg);
          } catch (e) {
            print('Error parsing WebSocket message: $e');
          }
        },
        onError: (error) {
          print('WebSocket error: $error');
        },
        onDone: () {
          print('WebSocket closed');
        },
      );
    } catch (e) {
      print('Error connecting to WebSocket: $e');
    }
  }

  static void send(String event, Map<String, dynamic> data) {
    _channel?.sink.add(json.encode({'event': event, 'data': data}));
  }

  static void register(String deviceId, String deviceName) {
    send('register', {'device_id': deviceId, 'device_name': deviceName});
  }

  static void setPlayer(String deviceId) {
    send('set_player', {'device_id': deviceId});
  }

  static void control(String action, {int? position}) {
    final data = <String, dynamic>{'action': action};
    if (position != null) data['position'] = position;
    send('control', data);
  }

  static void setVolume(double volume) {
    send('set_volume', {'volume': volume});
  }

  static void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }

  static bool get isConnected => _channel != null;
}