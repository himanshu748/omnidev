import SwiftUI

/// The OmniDev brand accent — electric blue, matching `--accent` on the web.
extension Color {
    static let omniAccent = Color(red: 0x4D / 255, green: 0xA2 / 255, blue: 0xFF / 255)
}

/// Native rendering of the OmniDev brand mark — the nested "secure
/// enclosure" from `frontend/app/components/Logo.tsx`, same geometry
/// (24-unit grid), so the brand reads identically on every surface.
struct LogoMarkView: View {
    var size: CGFloat = 26
    var color: Color = .omniAccent

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 5.5 / 24, style: .continuous)
                .stroke(color.opacity(0.85), lineWidth: size * 1.6 / 24)
                .frame(width: size * 18.5 / 24, height: size * 18.5 / 24)
            RoundedRectangle(cornerRadius: size * 2.4 / 24, style: .continuous)
                .fill(color)
                .frame(width: size * 8 / 24, height: size * 8 / 24)
        }
        .frame(width: size, height: size)
        .accessibilityHidden(true)
    }
}
