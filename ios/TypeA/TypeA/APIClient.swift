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
    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }()

    private init() {}

    func request<T: Decodable>(_ path: String, method: String = "GET") async throws -> T {
        try await send(path: path, method: method, body: Optional<EmptyBody>.none)
    }

    func request<T: Decodable, Body: Encodable>(
        _ path: String,
        method: String,
        body: Body
    ) async throws -> T {
        try await send(path: path, method: method, body: body)
    }

    private func send<T: Decodable, Body: Encodable>(
        path: String,
        method: String,
        body: Body?
    ) async throws -> T {
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = method
        if let token = await AuthService.shared.currentAccessToken() {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = try encoder.encode(body)
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

private struct EmptyBody: Encodable {}
