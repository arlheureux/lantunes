import 'package:flutter/foundation.dart';
import '../api/client.dart';
import '../models/album.dart';
import '../models/artist.dart';
import '../models/track.dart';

class LibraryProvider extends ChangeNotifier {
  List<Album> _albums = [];
  List<Artist> _artists = [];
  List<Track> _tracks = [];
  List<dynamic> _playlists = [];
  bool _isLoading = false;
  String _searchQuery = '';
  Map<String, dynamic> _searchResults = {'tracks': [], 'albums': [], 'artists': []};

  List<Album> get albums => _albums;
  List<Artist> get artists => _artists;
  List<Track> get tracks => _tracks;
  List<dynamic> get playlists => _playlists;
  bool get isLoading => _isLoading;
  String get searchQuery => _searchQuery;
  Map<String, dynamic> get searchResults => _searchResults;

  Future<void> loadAlbums() async {
    _isLoading = true;
    notifyListeners();

    final data = await ApiClient.getAlbums();
    _albums = data.map((json) => Album.fromJson(json)).toList();

    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadArtists() async {
    _isLoading = true;
    notifyListeners();

    final data = await ApiClient.getArtists();
    _artists = data.map((json) => Artist.fromJson(json)).toList();

    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadTracks({int page = 1}) async {
    _isLoading = true;
    notifyListeners();

    final data = await ApiClient.getTracks(page: page, limit: 50);
    _tracks = (data['tracks'] as List).map((json) => Track.fromJson(json)).toList();

    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadPlaylists() async {
    final data = await ApiClient.getPlaylists();
    _playlists = data;
    notifyListeners();
  }

  Future<void> search(String query) async {
    _searchQuery = query;
    if (query.isEmpty) {
      _searchResults = {'tracks': [], 'albums': [], 'artists': []};
      notifyListeners();
      return;
    }

    _isLoading = true;
    notifyListeners();

    _searchResults = await ApiClient.search(query);
    _searchResults['tracks'] = (_searchResults['tracks'] as List).map((t) => Track.fromJson(t)).toList();
    _searchResults['albums'] = (_searchResults['albums'] as List).map((a) => Album.fromJson(a)).toList();
    _searchResults['artists'] = (_searchResults['artists'] as List).map((a) => Artist.fromJson(a)).toList();

    _isLoading = false;
    notifyListeners();
  }

  Future<Map<String, dynamic>?> getAlbumDetails(int albumId) async {
    return await ApiClient.getAlbum(albumId);
  }

  Future<Map<String, dynamic>?> getArtistDetails(int artistId) async {
    return await ApiClient.getArtist(artistId);
  }

  void clearSearch() {
    _searchQuery = '';
    _searchResults = {'tracks': [], 'albums': [], 'artists': []};
    notifyListeners();
  }
}