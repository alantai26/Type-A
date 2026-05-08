import SwiftUI

struct FeedView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Spacer()

                Image(systemName: "newspaper")
                    .font(.system(size: 32, weight: .medium))
                    .foregroundStyle(Color.accentColor)
                    .frame(width: 72, height: 72)
                    .background(Color.accentColor.opacity(0.12))
                    .clipShape(Circle())

                VStack(spacing: 6) {
                    Text("Coming soon")
                        .font(.system(size: 24, weight: .bold, design: .rounded))
                    Text("See what your friends are rating, saving, and planning")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }

                Spacer()
            }
            .padding(.horizontal, 24)
            .navigationTitle("Feed")
        }
    }
}
