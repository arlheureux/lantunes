import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api/client.dart';
import '../models/album.dart';
import '../models/track.dart';
import '../providers/playback_provider.dart';

class AlbumScreen extends StatefulWidget {
  final Album album;

  const AlbumScreen({super.key, required this.album});

  @override
  State<AlbumScreen> createState() => _AlbumScreenState();
}

class _AlbumScreenState extends State<AlbumScreen> {
  List<Track> _tracks = [];
  String? _artistName;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAlbumDetails();
  }

  Future<void> _loadAlbumDetails() async {
    final library = context.read<dynamic>();
    final details = await library.getAlbumDetails(widget.album.id);
    
    if (details != null && mounted) {
      setState(() {
        _tracks = (details['tracks'] as List?)?.map((t) => Track.fromJson(t)).toList() ?? [];
        _artistName = details['artist']?['name'];
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.album.title),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Container(
                        width: 200,
                        height: 200,
                        decoration: BoxDecoration(
                          color: Colors.grey[800],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Center(
                          child: Icon(Icons.album, size: 80, color: Colors.grey),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        widget.album.title,
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      if (_artistName != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          _artistName!,
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.grey[400],
                          ),
                        ),
                      ],
                      if (widget.album.year != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          '${widget.album.year}',
                          style: TextStyle(color: Colors.grey[500]),
                        ),
                      ],
                    ],
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: _tracks.length,
                    itemBuilder: (context, index) {
                      final track = _tracks[index];
                      return ListTile(
                        leading: Text(
                          '${track.trackNumber ?? index + 1}',
                          style: TextStyle(color: Colors.grey[500]),
                        ),
                        title: Text(track.title),
                        subtitle: Text(track.durationString),
                        trailing: const Icon(Icons.play_arrow),
                        onTap: () {
                          context.read<PlaybackProvider>().playTrack(track);
                        },
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }
}