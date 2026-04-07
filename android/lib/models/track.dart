class Track {
  final int id;
  final String title;
  final int? albumId;
  final int? artistId;
  final int? discNumber;
  final int? trackNumber;
  final int? duration;
  final String? path;
  final String? fileFormat;
  final int? bitrate;
  final int? sampleRate;

  Track({
    required this.id,
    required this.title,
    this.albumId,
    this.artistId,
    this.discNumber,
    this.trackNumber,
    this.duration,
    this.path,
    this.fileFormat,
    this.bitrate,
    this.sampleRate,
  });

  factory Track.fromJson(Map<String, dynamic> json) {
    return Track(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      albumId: json['album_id'],
      artistId: json['artist_id'],
      discNumber: json['disc_number'],
      trackNumber: json['track_number'],
      duration: json['duration'],
      path: json['path'],
      fileFormat: json['file_format'],
      bitrate: json['bitrate'],
      sampleRate: json['sample_rate'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'album_id': albumId,
    'artist_id': artistId,
    'disc_number': discNumber,
    'track_number': trackNumber,
    'duration': duration,
    'path': path,
    'file_format': fileFormat,
    'bitrate': bitrate,
    'sample_rate': sampleRate,
  };

  String get durationString {
    if (duration == null) return '0:00';
    final minutes = duration! ~/ 60;
    final seconds = duration! % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }
}