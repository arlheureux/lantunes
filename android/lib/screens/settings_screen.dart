import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api/client.dart';
import '../providers/playback_provider.dart';

class SettingsScreen extends StatefulWidget {
  final bool initialSetup;

  const SettingsScreen({super.key, this.initialSetup = false});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadUrl();
  }

  Future<void> _loadUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final url = prefs.getString('server_url');
    if (url != null) {
      _urlController.text = url;
    }
  }

  Future<void> _saveUrl() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      setState(() => _error = 'Please enter a server URL');
      return;
    }

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setState(() => _error = 'URL must start with http:// or https://');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Set the URL and test connection
      ApiClient.setBaseUrl(url);
      
      // Try to fetch albums to test connection
      await ApiClient.getAlbums();
      
      // Save to preferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('server_url', url);
      
      // Initialize playback provider
      if (mounted) {
        await context.read<PlaybackProvider>().init(url);
        
        setState(() => _isLoading = false);
        
        if (widget.initialSetup && mounted) {
          Navigator.of(context).pushReplacementNamed('/');
        }
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = 'Could not connect to server: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: widget.initialSetup ? null : AppBar(title: const Text('Settings')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (widget.initialSetup) ...[
              const Icon(Icons.music_note, size: 64, color: Colors.purple),
              const SizedBox(height: 24),
              const Text(
                'Welcome to LanTunes',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                'Enter your server URL to get started',
                style: TextStyle(color: Colors.grey[400]),
              ),
              const SizedBox(height: 32),
            ],
            TextField(
              controller: _urlController,
              decoration: InputDecoration(
                labelText: 'Server URL',
                hintText: 'http://192.168.1.100:8080',
                errorText: _error,
                prefixIcon: const Icon(Icons.link),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              keyboardType: TextInputType.url,
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _saveUrl,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purple,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(widget.initialSetup ? 'Connect' : 'Save'),
              ),
            ),
            const SizedBox(height: 24),
            const Divider(),
            const SizedBox(height: 16),
            Text(
              'Example: http://192.168.0.85:8080',
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }
}