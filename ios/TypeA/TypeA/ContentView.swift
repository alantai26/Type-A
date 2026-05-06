import SwiftUI

struct ContentView: View {
    @State private var status: String = "Tap to ping /health"
    @State private var isLoading = false

    var body: some View {
        VStack(spacing: 20) {
            Text("Type A")
                .font(.largeTitle)
                .bold()

            Button {
                Task { await ping() }
            } label: {
                if isLoading {
                    ProgressView()
                } else {
                    Text("Ping /health")
                }
            }
            .disabled(isLoading)
            .buttonStyle(.borderedProminent)

            Text(status)
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding()
    }

    func ping() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let health: Health = try await APIClient.shared.request("/health")
            status = "200 OK — status: \(health.status)"
        } catch let error as APIError {
            status = "HTTP \(error.statusCode): \(error.body)"
        } catch {
            status = "Network error: \(error.localizedDescription)"
        }
    }
}

#Preview {
    ContentView()
}
