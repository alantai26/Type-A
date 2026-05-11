import SwiftUI

@main
struct TypeAApp: App {
    @State private var authStore = AuthStore()
    @State private var tabSelection = TabSelectionStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(authStore)
                .environment(tabSelection)
        }
    }
}
