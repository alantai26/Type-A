import SwiftUI

struct SearchView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Spacer()

                Image(systemName: "magnifyingglass")
                    .font(.system(size: 32, weight: .medium))
                    .foregroundStyle(Color.accentColor)
                    .frame(width: 72, height: 72)
                    .background(Color.accentColor.opacity(0.12))
                    .clipShape(Circle())

                VStack(spacing: 6) {
                    Text("Coming soon")
                        .font(.system(size: 24, weight: .bold, design: .rounded))
                    Text("Find places worth trying, ranked by what you'll actually like.")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }

                Spacer()
            }
            .padding(.horizontal, 24)
            .navigationTitle("Search")
        }
    }
}
