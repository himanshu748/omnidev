import SwiftUI

/// The OmniDev brand accent — electric blue.
extension Color {
    static let omniAccent = Color(red: 0x4D / 255, green: 0xA2 / 255, blue: 0xFF / 255)
}

/// The in-app brand badge: a terminal glyph on a blue tile, echoing the
/// terminal-prompt logo (the app icon).
struct LogoMarkView: View {
    var size: CGFloat = 26
    var color: Color = .omniAccent

    var body: some View {
        Image(systemName: "terminal.fill")
            .font(.system(size: size * 0.52, weight: .semibold))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(color.gradient, in: RoundedRectangle(cornerRadius: size * 0.24, style: .continuous))
            .accessibilityHidden(true)
    }
}
