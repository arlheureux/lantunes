import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/library_provider.dart';
import '../providers/playback_provider.dart';
import 'album_screen.dart';
import 'now_playing_screen.dart';
import 'settings_screen.dart';
import '../widgets/player_bar.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final library = context.read<LibraryProvider>();
    await Future.wait([
      library.loadAlbums(),
      library.loadArtists(),
      library.loadTracks(),
      library.loadPlaylists(),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('LanTunes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: const [
          _LibraryView(),
          _SearchView(),
          _QueueView(),
        ],
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const PlayerBar(),
          BottomNavigationBar(
            currentIndex: _currentIndex,
            onTap: (index) => setState(() => _currentIndex = index),
            items: const [
              BottomNavigationBarItem(icon: Icon(Icons.library_music), label: 'Library'),
              BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
              BottomNavigationBarItem(icon: Icon(Icons.queue_music), label: 'Queue'),
            ],
          ),
        ],
      ),
    );
  }
}

class _LibraryView extends StatelessWidget {
  const _LibraryView();

  @override
  Widget build(BuildContext context) {
    final library = context.watch<LibraryProvider>();
    
    return DefaultTabController(
      length: 3,
      child: Column(
        children: [
          const TabBar(
            tabs: [
              Tab(text: 'Albums'),
              Tab(text: 'Artists'),
              Tab(text: 'Tracks'),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _AlbumsTab(),
                _ArtistsTab(),
                _TracksTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AlbumsTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final library = context.watch<LibraryProvider>();
    
    if (library.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (library.albums.isEmpty) {
      return const Center(child: Text('No albums found'));
    }
    
    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.8,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
      ),
      itemCount: library.albums.length,
      itemBuilder: (context, index) {
        final album = library.albums[index];
        return GestureDetector(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => AlbumScreen(album: album),
              ),
            );
          },
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.grey[800],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Center(
                    child: Icon(Icons.album, size: 48, color: Colors.grey),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                album.title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ArtistsTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final library = context.watch<LibraryProvider>();
    
    if (library.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (library.artists.isEmpty) {
      return const Center(child: Text('No artists found'));
    }
    
    return ListView.builder(
      itemCount: library.artists.length,
      itemBuilder: (context, index) {
        final artist = library.artists[index];
        return ListTile(
          leading: const CircleAvatar(
            child: Icon(Icons.person),
          ),
          title: Text(artist.name),
          onTap: () {
            // TODO: Navigate to artist details
          },
        );
      },
    );
  }
}

class _TracksTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final library = context.watch<LibraryProvider>();
    final playback = context.read<PlaybackProvider>();
    
    if (library.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (library.tracks.isEmpty) {
      return const Center(child: Text('No tracks found'));
    }
    
    return ListView.builder(
      itemCount: library.tracks.length,
      itemBuilder: (context, index) {
        final track = library.tracks[index];
        return ListTile(
          title: Text(track.title, maxLines: 1, overflow: TextOverflow.ellipsis),
          subtitle: Text(track.durationString),
          trailing: const Icon(Icons.play_arrow),
          onTap: () {
            playback.playTrack(track);
          },
        );
      },
    );
  }
}

class _SearchView extends StatefulWidget {
  const _SearchView();

  @override
  State<_SearchView> createState() => _SearchViewState();
}

class _SearchViewState extends State<_SearchView> {
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final library = context.watch<LibraryProvider>();
    
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Search...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _searchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        _searchController.clear();
                        library.clearSearch();
                      },
                    )
                  : null,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            onChanged: (value) {
              library.search(value);
            },
          ),
        ),
        Expanded(
          child: _searchController.text.isEmpty
              ? const Center(child: Text('Search for music'))
              : _SearchResults(),
        ),
      ],
    );
  }
}

class _SearchResults extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final library = context.watch<LibraryProvider>();
    final playback = context.read<PlaybackProvider>();
    final results = library.searchResults;
    final tracks = results['tracks'] as List;
    
    if (tracks.isEmpty && library.searchQuery.isNotEmpty) {
      return const Center(child: Text('No results found'));
    }
    
    return ListView.builder(
      itemCount: tracks.length,
      itemBuilder: (context, index) {
        final track = tracks[index];
        return ListTile(
          title: Text(track.title, maxLines: 1, overflow: TextOverflow.ellipsis),
          trailing: const Icon(Icons.play_arrow),
          onTap: () {
            playback.playTrack(track);
          },
        );
      },
    );
  }
}

class _QueueView extends StatelessWidget {
  const _QueueView();

  @override
  Widget build(BuildContext context) {
    final playback = context.watch<PlaybackProvider>();
    final queue = playback.state.queue;
    
    if (queue.isEmpty) {
      return const Center(child: Text('Queue is empty'));
    }
    
    return ListView.builder(
      itemCount: queue.length,
      itemBuilder: (context, index) {
        return ListTile(
          leading: Text('${index + 1}'),
          title: Text('Track ${queue[index]}'),
        );
      },
    );
  }
}