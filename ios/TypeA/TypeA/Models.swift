import Foundation

struct Health: Decodable {
    let status: String
}

struct User: Decodable {
    let userId: UUID
    let email: String
    let displayName: String
    let createdAt: Date
}

struct Place: Decodable {
    let placeId: UUID
    let name: String
    let latitude: Double
    let longitude: Double
    let distanceM: Double
    let isSaved: Bool
}

struct Event: Decodable {
    let eventId: UUID
    let creatorId: UUID
    let placeId: UUID?
    let customLocationName: String?
    let outingId: UUID?
    let sequencePosition: Int?
    let status: String
    let scheduledFor: Date?
    let completedAt: Date?
    let weight: Double?
}

struct Outing: Decodable {
    let outingId: UUID
    let creatorId: UUID
    let title: String
    let status: String
    let scheduledFor: Date?
    let completedAt: Date?
    let finalRating: Double?
    let derivedScore: Double?
    let events: [Event]
}

struct Friend: Decodable {
    let userId: UUID
    let displayName: String
    let createdAt: Date
}

enum FeedItem: Decodable {
    case rating(FeedRating)
    case save(FeedSave)
    case outing(FeedOuting)

    private enum DiscriminatorKey: String, CodingKey {
        case type
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: DiscriminatorKey.self)
        let type = try container.decode(String.self, forKey: .type)
        switch type {
        case "rating":
            self = .rating(try FeedRating(from: decoder))
        case "save":
            self = .save(try FeedSave(from: decoder))
        case "outing":
            self = .outing(try FeedOuting(from: decoder))
        default:
            throw DecodingError.dataCorruptedError(
                forKey: .type,
                in: container,
                debugDescription: "Unknown feed item type: \(type)"
            )
        }
    }
}

struct FeedRating: Decodable {
    let actorId: UUID
    let displayName: String
    let placeId: UUID
    let placeName: String
    let rating: Double
    let createdAt: Date
}

struct FeedSave: Decodable {
    let actorId: UUID
    let displayName: String
    let placeId: UUID
    let placeName: String
    let createdAt: Date
}

struct FeedOuting: Decodable {
    let actorId: UUID
    let outingId: UUID
    let displayName: String
    let title: String
    let finalRating: Double
    let createdAt: Date
}

struct FeedResponse: Decodable {
    let items: [FeedItem]
    let nextCursor: Date?
}
