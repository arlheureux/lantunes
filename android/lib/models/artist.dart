class Artist {
  final int id;
  final String name;
  final String? sortName;
  final String? artworkPath;

  Artist({
    required this.id,
    required this.name,
    this.sortName,
    this.artworkPath,
  });

  factory Artist.fromJson(Map<String, dynamic> json) {
    return Artist(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      sortName: json['sort_name'],
      artworkPath: json['artwork_path'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'sort_name': sortName,
    'artwork_path': artworkPath,
  };
}