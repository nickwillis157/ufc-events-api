import Foundation

class NetworkService: ObservableObject {
    static let shared = NetworkService()
    private let baseURL = "http://127.0.0.1:8000/api"
    
    private init() {}
    
    func fetchEvents() async throws -> [UFCEvent] {
        guard let url = URL(string: "\(baseURL)/events") else {
            throw NetworkError.invalidURL
        }
        
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let decoder = JSONDecoder()
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        decoder.dateDecodingStrategy = .formatted(dateFormatter)
        
        return try decoder.decode([UFCEvent].self, from: data)
    }
    
    func fetchUpcomingEvents() async throws -> [UFCEvent] {
        guard let url = URL(string: "\(baseURL)/events/upcoming") else {
            throw NetworkError.invalidURL
        }
        
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let decoder = JSONDecoder()
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        decoder.dateDecodingStrategy = .formatted(dateFormatter)
        
        let events = try decoder.decode([UFCEvent].self, from: data)
        print("🌐 NetworkService.fetchUpcomingEvents() received \(events.count) events")
        for event in events.prefix(3) {
            print("  - \(event.eventName) on \(event.eventDate)")
        }
        return events
    }
    
    func fetchRecentEvents() async throws -> [UFCEvent] {
        guard let url = URL(string: "\(baseURL)/events/recent") else {
            throw NetworkError.invalidURL
        }
        
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let decoder = JSONDecoder()
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        decoder.dateDecodingStrategy = .formatted(dateFormatter)
        
        return try decoder.decode([UFCEvent].self, from: data)
    }
    
    func fetchEvent(id: String) async throws -> UFCEvent {
        guard let url = URL(string: "\(baseURL)/events/\(id)") else {
            throw NetworkError.invalidURL
        }
        
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let decoder = JSONDecoder()
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        decoder.dateDecodingStrategy = .formatted(dateFormatter)
        
        return try decoder.decode(UFCEvent.self, from: data)
    }
}

enum NetworkError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case noData
    case decodingError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .noData:
            return "No data received"
        case .decodingError:
            return "Failed to decode data"
        }
    }
}