const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
  // Enable closing confirmation
  if (tg.enableClosingConfirmation) {
    tg.enableClosingConfirmation();
  }
}

// Haptic feedback helper
const haptic = {
  impact: (style = "light") => {
    if (tg?.HapticFeedback) {
      tg.HapticFeedback.impactOccurred(style);
    }
  },
  notification: (type = "success") => {
    if (tg?.HapticFeedback) {
      tg.HapticFeedback.notificationOccurred(type);
    }
  },
  selection: () => {
    if (tg?.HapticFeedback) {
      tg.HapticFeedback.selectionChanged();
    }
  }
};
