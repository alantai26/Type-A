import Foundation

struct APIError: Error {
    let statusCode: Int
    let body: String
}

final class APIClient {
    static let shared = APIClient()

    let baseURL = AppConfig.apiBaseURL
    private let session = URLSession.shared
    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()

    private init() {}

    func request<T: Decodable>(_ path: String, method: String = "GET") async throws -> T {
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = method
        if let token = KeychainStore.shared.get("auth_token") {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let (data, response) = try await session.data(for: req)
        guard let http = response as? HTTPURLResponse else {
            throw APIError(statusCode: -1, body: "no response")
        }
        guard (200..<300).contains(http.statusCode) else {
            throw APIError(
                statusCode: http.statusCode,
                body: String(data: data, encoding: .utf8) ?? ""
            )
        }
        return try decoder.decode(T.self, from: data)
    }
}
