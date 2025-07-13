import Foundation

// MARK: - UFCEvent Model
struct UFCEvent: Identifiable, Codable {
    let id: String
    let eventName: String
    let eventDate: Date
    let venue: String?
    let location: String?
    let status: EventStatus
    let fights: [Fight]
    
    enum CodingKeys: String, CodingKey {
        case id = "event_id"
        case eventName = "event_name"
        case eventDate = "event_date"
        case venue
        case location
        case status
        case fights
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        id = try container.decode(String.self, forKey: .id)
        eventName = try container.decode(String.self, forKey: .eventName)
        venue = try container.decodeIfPresent(String.self, forKey: .venue)
        location = try container.decodeIfPresent(String.self, forKey: .location)
        status = try container.decode(EventStatus.self, forKey: .status)
        fights = try container.decode([Fight].self, forKey: .fights)
        
        let dateString = try container.decode(String.self, forKey: .eventDate)
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        eventDate = formatter.date(from: dateString) ?? Date()
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        
        try container.encode(id, forKey: .id)
        try container.encode(eventName, forKey: .eventName)
        try container.encodeIfPresent(venue, forKey: .venue)
        try container.encodeIfPresent(location, forKey: .location)
        try container.encode(status, forKey: .status)
        try container.encode(fights, forKey: .fights)
        
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        try container.encode(formatter.string(from: eventDate), forKey: .eventDate)
    }
}

// MARK: - Event Status
enum EventStatus: String, Codable, CaseIterable {
    case scheduled = "scheduled"
    case completed = "completed"
    case cancelled = "cancelled"
    case postponed = "postponed"
    
    var displayName: String {
        switch self {
        case .scheduled: return "Scheduled"
        case .completed: return "Completed"
        case .cancelled: return "Cancelled"
        case .postponed: return "Postponed"
        }
    }
}

// MARK: - Fight Model
struct Fight: Identifiable, Codable {
    let id = UUID()
    let boutOrder: Int
    let fighter1: Fighter
    let fighter2: Fighter
    let weightClass: String
    let titleFight: TitleFight
    let method: String?
    let winner: String?
    let segment: FightSegment?
    
    enum CodingKeys: String, CodingKey {
        case boutOrder = "bout_order"
        case fighter1
        case fighter2
        case weightClass = "weight_class"
        case titleFight = "title_fight"
        case method
        case winner
        case segment
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        boutOrder = try container.decode(Int.self, forKey: .boutOrder)
        fighter1 = try container.decode(Fighter.self, forKey: .fighter1)
        fighter2 = try container.decode(Fighter.self, forKey: .fighter2)
        weightClass = try container.decode(String.self, forKey: .weightClass)
        method = try container.decodeIfPresent(String.self, forKey: .method)
        winner = try container.decodeIfPresent(String.self, forKey: .winner)
        segment = try container.decodeIfPresent(FightSegment.self, forKey: .segment)
        
        let titleFightString = try container.decode(String.self, forKey: .titleFight)
        titleFight = TitleFight(rawValue: titleFightString) ?? .none
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        
        try container.encode(boutOrder, forKey: .boutOrder)
        try container.encode(fighter1, forKey: .fighter1)
        try container.encode(fighter2, forKey: .fighter2)
        try container.encode(weightClass, forKey: .weightClass)
        try container.encodeIfPresent(method, forKey: .method)
        try container.encodeIfPresent(winner, forKey: .winner)
        try container.encodeIfPresent(segment, forKey: .segment)
        try container.encode(titleFight.rawValue, forKey: .titleFight)
    }
}

// MARK: - Fighter Model
struct Fighter: Codable {
    let name: String
    let record: String?
    let rank: Int?
    let country: String?
}

// MARK: - Title Fight Type
enum TitleFight: String, Codable {
    case none = "none"
    case undisputed = "undisputed"
    case interim = "interim"
    
    var displayName: String {
        switch self {
        case .none: return "Regular Fight"
        case .undisputed: return "Title Fight"
        case .interim: return "Interim Title Fight"
        }
    }
}

// MARK: - Fight Segment
enum FightSegment: String, Codable {
    case mainCard = "main-card"
    case prelims = "prelims"
    case earlyPrelims = "early-prelims"
    
    var displayName: String {
        switch self {
        case .mainCard: return "Main Card"
        case .prelims: return "Preliminary Card"
        case .earlyPrelims: return "Early Preliminary Card"
        }
    }
}

// MARK: - Sample Data
extension UFCEvent {
    static var sampleData: [UFCEvent] {
        guard let url = Bundle.main.url(forResource: "UFC_SampleData", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let events = try? JSONDecoder().decode([UFCEvent].self, from: data) else {
            return []
        }
        return events
    }
}