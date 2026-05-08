import SwiftUI

struct RootView: View {
    @Environment(AuthStore.self) private var authStore

    var body: some View {
        Group {
            if authStore.isInitializing {
                ProgressView("Loading...")
            } else if authStore.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
    }
}
