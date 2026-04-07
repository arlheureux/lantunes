import 'package:dio/dio.dart';

class ApiClient {
  static String? _baseUrl;
  static final Dio _dio = Dio();

  static void setBaseUrl(String url) {
    _baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
    _dio.options.baseUrl = _baseUrl!;
    _dio.options.connectTimeout = const Duration(seconds: 10);
    _dio.options.receiveTimeout = const Duration(seconds: 30);
  }

  static String? get baseUrl => _baseUrl;

  // Albums
  static Future<List<dynamic>> getAlbums() async {
    try {
      final response = await _dio.get('/api/library/albums');
      return response.data;
    } catch (e) {
      print('Error fetching albums: $e');
      return [];
    }
  }

  // Artists
  static Future<List<dynamic>> getArtists() async {
    try {
      final response = await _dio.get('/api/library/artists');
      return response.data;
    } catch (e) {
      print('Error fetching artists: $e');
      return [];
    }
  }

  // Tracks
  static Future<Map<String, dynamic>> getTracks({int page = 1, int limit = 50}) async {
    try {
      final response = await _dio.get('/api/library/tracks', queryParameters: {
        'page': page,
        'limit': limit,
      });
      return response.data;
    } catch (e) {
      print('Error fetching tracks: $e');
      return {'tracks': [], 'total': 0, 'pages': 0};
    }
  }

  // Search
  static Future<Map<String, dynamic>> search(String query) async {
    try {
      final response = await _dio.get('/api/library/search', queryParameters: {'q': query});
      return response.data;
    } catch (e) {
      print('Error searching: $e');
      return {'tracks': [], 'albums': [], 'artists': []};
    }
  }

  // Playback state
  static Future<Map<String, dynamic>?> getPlaybackState({String? player}) async {
    try {
      final params = player != null ? {'player': player} : null;
      final response = await _dio.get('/api/playback/state', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error fetching playback state: $e');
      return null;
    }
  }

  // Play track
  static Future<Map<String, dynamic>?> playTrack({int? trackId, String? player}) async {
    try {
      final params = <String, dynamic>{};
      if (trackId != null) params['track_id'] = trackId;
      if (player != null) params['player'] = player;
      final response = await _dio.post('/api/playback/play', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error playing track: $e');
      return null;
    }
  }

  // Pause
  static Future<Map<String, dynamic>?> pause({String? player}) async {
    try {
      final params = player != null ? {'player': player} : null;
      final response = await _dio.post('/api/playback/pause', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error pausing: $e');
      return null;
    }
  }

  // Next
  static Future<Map<String, dynamic>?> next({String? player}) async {
    try {
      final params = player != null ? {'player': player} : null;
      final response = await _dio.post('/api/playback/next', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error next: $e');
      return null;
    }
  }

  // Previous
  static Future<Map<String, dynamic>?> previous({String? player}) async {
    try {
      final params = player != null ? {'player': player} : null;
      final response = await _dio.post('/api/playback/previous', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error previous: $e');
      return null;
    }
  }

  // Seek
  static Future<Map<String, dynamic>?> seek(int position, {String? player}) async {
    try {
      final params = <String, dynamic>{'position': position};
      if (player != null) params['player'] = player;
      final response = await _dio.post('/api/playback/seek', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error seeking: $e');
      return null;
    }
  }

  // Set volume
  static Future<Map<String, dynamic>?> setVolume(double volume, {String? player}) async {
    try {
      final params = <String, dynamic>{'volume': volume};
      if (player != null) params['player'] = player;
      final response = await _dio.post('/api/playback/volume', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error setting volume: $e');
      return null;
    }
  }

  // Toggle shuffle
  static Future<Map<String, dynamic>?> toggleShuffle({String? player}) async {
    try {
      final params = player != null ? {'player': player} : null;
      final response = await _dio.post('/api/playback/shuffle', queryParameters: params);
      return response.data;
    } catch (e) {
      print('Error toggling shuffle: $e');
      return null;
    }
  }

  // Playlists
  static Future<List<dynamic>> getPlaylists() async {
    try {
      final response = await _dio.get('/api/playlists');
      return response.data;
    } catch (e) {
      print('Error fetching playlists: $e');
      return [];
    }
  }

  // Get album details
  static Future<Map<String, dynamic>?> getAlbum(int albumId) async {
    try {
      final response = await _dio.get('/api/library/albums/$albumId');
      return response.data;
    } catch (e) {
      print('Error fetching album: $e');
      return null;
    }
  }

  // Get artist details
  static Future<Map<String, dynamic>?> getArtist(int artistId) async {
    try {
      final response = await _dio.get('/api/library/artists/$artistId');
      return response.data;
    } catch (e) {
      print('Error fetching artist: $e');
      return null;
    }
  }

  // Get stream URL
  static String getStreamUrl(int trackId) {
    return '${_baseUrl ?? ""}/api/playback/stream/$trackId';
  }

  // Get artwork URL
  static String getArtworkUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    return '${_baseUrl ?? ""}$path';
  }
}