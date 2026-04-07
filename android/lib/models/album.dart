class Album {
  final int id;
  final String title;
  final int? artistId;
  final int? year;
  final String? genre;
  final String? artworkPath;

  Album({
    required this.id,
    required this.title,
    this.artistId,
    this.year,
    this.genre,
    this.artworkPath,
  });

  factory Album.fromJson(Map<String, dynamic> json) {
    return Album(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      artistId: json['artist_id'],
      year: json['year'],
      genre: json['genre'],
      artworkPath: json['artwork_path'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'artist_id': artistId,
    'year': year,
    'genre': genre,
    'artwork_path': artworkPath,
  };
}