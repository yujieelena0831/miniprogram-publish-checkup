# Navigation And TabBar

Do not choose a tabBar implementation before inspecting the product navigation and existing code.

## Built-In TabBar

- Prefer the built-in tabBar when standard text/icon navigation is sufficient.
- Verify every `pagePath` is a top-level page declared in `app.json`.
- Verify `iconPath` and `selectedIconPath` files exist when configured.
- Use `wx.switchTab` for tab pages; do not rely on ordinary navigation APIs for those routes.

## Custom TabBar

- Use `tabBar.custom = true` only when the design or interaction requires it.
- Verify `custom-tab-bar/index` companion files exist and compile.
- Keep selected state synchronized in each tab page lifecycle.
- Test safe-area padding, keyboard behavior, page re-entry, dark mode if supported, and iOS/Android differences.
- Do not assume a text-only or icon-based design; follow the actual product requirements.

## Navigation Checks

- Verify navigate, redirect, relaunch, back, and switch-tab targets exist.
- Test direct entry from QR codes, sharing, favorites, scene parameters, and deep links used by the product.
- Confirm subpackage routes load before dependent code executes.
- Verify navigation remains usable after login expiry, permission denial, empty data, and network failure.
- Test on a real device because simulator layout and component rendering can differ.
