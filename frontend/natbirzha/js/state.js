/**
 * Reactive State Management for Natbirzha
 */

class NatStateStore {
  constructor() {
    this.user = null;
    this.company = null;
    this.inventory = {};
    this.factories = [];
    this.nav = 0;
    this.currentTab = 'overview';
    this.listeners = new Set();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    for (const listener of this.listeners) {
      try {
        listener(this);
      } catch (err) {
        console.error('State listener error:', err);
      }
    }
  }

  setUser(user) {
    this.user = user;
    this.notify();
  }

  setCompany(companyData) {
    if (!companyData) {
      this.company = null;
      this.inventory = {};
      this.factories = [];
      this.nav = 0;
    } else {
      this.company = companyData;
      this.inventory = companyData.inventory || {};
      this.factories = companyData.factories || [];
      this.nav = companyData.nav || 0;
    }
    this.notify();
  }

  updateCompany(partial) {
    if (this.company) {
      this.company = { ...this.company, ...partial };
      if (partial.inventory) this.inventory = partial.inventory;
      if (partial.factories) this.factories = partial.factories;
      if (partial.nav !== undefined) this.nav = partial.nav;
      this.notify();
    }
  }

  setTab(tab) {
    this.currentTab = tab;
    this.notify();
  }

  hasCompany() {
    return !!this.company && !!this.company.id;
  }
}

export const store = new NatStateStore();
