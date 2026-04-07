import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/playback_provider.dart';
import '../screens/now_playing_screen.dart';

class PlayerBar extends StatelessWidget {
  const PlayerBar({super.key});

  @override
  Widget build(BuildContext context) {
    final playback = context.watch<PlaybackProvider>();
    final state = playback.state;

    if (state.track == null) {
      return const SizedBox.shrink();
    }

    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const NowPlayingScreen()),
        );
      },
      child: Container(
        height: 64,
        color: const Color(0xFF282828),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            // Track info
            Expanded(
              flex: 3,
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: Colors.grey[800],
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Icon(Icons.music_note, color: Colors.grey),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          state.track!.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (playback.devices.isNotEmpty) ...[
                          const SizedBox(height: 2),
                          Text(
                            'Playing on: ${playback.devices.firstWhere((d) => d.isPlayer, orElse: () => playback.devices.first).name}',
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.grey[500],
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            // Controls
            Expanded(
              flex: 4,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    icon: const Icon(Icons.skip_previous),
                    onPressed: () => playback.previous(),
                  ),
                  IconButton(
                    icon: Icon(state.isPlaying ? Icons.pause : Icons.play_arrow),
                    iconSize: 32,
                    onPressed: () {
                      if (state.isPlaying) {
                        playback.pause();
                      } else {
                        playback.play();
                      }
                    },
                  ),
                  IconButton(
                    icon: const Icon(Icons.skip_next),
                    onPressed: () => playback.next(),
                  ),
                ],
              ),
            ),
            // Volume / more
            Expanded(
              flex: 1,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (playback.devices.length > 1)
                    PopupMenuButton<String>(
                      icon: const Icon(Icons.devices, size: 20),
                      onSelected: (deviceId) {
                        playback.selectPlayer(deviceId);
                      },
                      itemBuilder: (context) => playback.devices
                          .map((d) => PopupMenuItem(
                                value: d.id,
                                child: Row(
                                  children: [
                                    Icon(
                                      d.isPlayer ? Icons.volume_up : Icons.phone_android,
                                      size: 18,
                                      color: d.isPlayer ? Colors.purple : null,
                                    ),
                                    const SizedBox(width: 8),
                                    Text(d.name),
                                    if (d.isPlayer) const Text(' (playing)', style: TextStyle(color: Colors.grey)),
                                  ],
                                ),
                              ))
                          .toList(),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}