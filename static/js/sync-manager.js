// مدير المزامنة للتعامل مع البيانات أثناء الاتصال وعدم الاتصال
class SyncManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.syncInProgress = false;
    this.lastSyncTime = null;
    this.maxRetries = 3;

    this.init();
  }

  init() {
    // مراقبة حالة الاتصال
    window.addEventListener("online", () => {
      this.isOnline = true;
      this.onConnectionRestored();
      this.updateOnlineStatus();
    });

    window.addEventListener("offline", () => {
      this.isOnline = false;
      this.onConnectionLost();
      this.updateOnlineStatus();
    });

    // مزامنة دورية كل 5 دقائق
    setInterval(() => {
      if (this.isOnline && !this.syncInProgress) {
        this.performSync();
      }
    }, 5 * 60 * 1000);

    this.updateOnlineStatus();
    this.loadLastSyncTime();
  }

  onConnectionRestored() {
    console.log("Connection restored - starting sync");
    this.showNotification("تم استعادة الاتصال - جاري المزامنة...", "success");
    setTimeout(() => this.performSync(), 1000);
  }

  onConnectionLost() {
    console.log("Connection lost - switching to offline mode");
    this.showNotification(
      "فقدان الاتصال - تم التبديل للوضع غير المتصل",
      "warning"
    );
    this.syncInProgress = false;
  }

  updateOnlineStatus() {
    const statusIndicator = document.querySelector(".network-status");
    if (statusIndicator) {
      if (this.isOnline) {
        statusIndicator.className = "network-status online";
        statusIndicator.innerHTML = '<i class="bi bi-wifi"></i> متصل';
      } else {
        statusIndicator.className = "network-status offline";
        statusIndicator.innerHTML = '<i class="bi bi-wifi-off"></i> غير متصل';
      }
    }
    this.updateLastSyncDisplay();
  }

  // المزامنة الرئيسية
  async performSync() {
    if (this.syncInProgress || !this.isOnline) return;

    this.syncInProgress = true;
    this.showSyncProgress(true);

    try {
      await this.syncDataFromServer();
      await this.syncPendingOperations();

      this.lastSyncTime = new Date();
      await this.saveLastSyncTime();

      this.showNotification("تمت المزامنة بنجاح", "success");
    } catch (error) {
      console.error("Sync failed:", error);
      this.showNotification("فشلت المزامنة - سيتم المحاولة مرة أخرى", "error");
    } finally {
      this.syncInProgress = false;
      this.showSyncProgress(false);
      this.updateLastSyncDisplay();
    }
  }

  async syncDataFromServer() {
    const endpoints = [
      { url: "/api/products", handler: "saveProducts" },
      { url: "/api/categories", handler: "saveCategories" },
      { url: "/api/customers", handler: "saveCustomers" },
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(endpoint.url);
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data)) {
            await window.dbManager[endpoint.handler](data);
          }
        }
      } catch (error) {
        console.error(`Failed to sync ${endpoint.url}:`, error);
      }
    }
  }

  async syncPendingOperations() {
    const pendingOps = await window.dbManager.getPendingOperations();

    for (const operation of pendingOps) {
      try {
        await this.processPendingOperation(operation);
        await window.dbManager.removePendingOperation(operation.id);
      } catch (error) {
        console.error("Failed to process operation:", error);
        operation.retry_count = (operation.retry_count || 0) + 1;
        if (operation.retry_count >= this.maxRetries) {
          await window.dbManager.removePendingOperation(operation.id);
        }
      }
    }
  }

  async processPendingOperation(operation) {
    if (operation.operation_type === "create_sale") {
      return await this.syncCreateSale(operation);
    }
  }

  async syncCreateSale(operation) {
    const response = await fetch("/api/sales", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": window.csrf_token || "",
      },
      body: JSON.stringify(operation.data),
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    return await response.json();
  }

  // حفظ البيانات محلياً
  async saveSaleLocal(saleData) {
    const saleId = await window.dbManager.saveSale(saleData);
    if (this.isOnline) {
      setTimeout(() => this.performSync(), 1000);
    }
    return saleId;
  }

  // واجهة المستخدم
  showSyncProgress(show) {
    const indicator = document.querySelector(".sync-indicator");
    if (indicator) {
      indicator.style.display = show ? "inline-block" : "none";
      if (show) {
        indicator.innerHTML =
          '<i class="bi bi-arrow-repeat"></i> جاري المزامنة...';
      }
    }
  }

  showNotification(message, type = "info") {
    const notification = document.createElement("div");
    notification.className = `alert alert-${type} notification-toast`;
    notification.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;

    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
  }

  updateLastSyncDisplay() {
    const syncDisplay = document.querySelector(".last-sync-time");
    if (syncDisplay && this.lastSyncTime) {
      const minutes = Math.floor((new Date() - this.lastSyncTime) / 60000);
      const timeAgo =
        minutes < 1
          ? "منذ لحظات"
          : minutes < 60
          ? `منذ ${minutes} دقيقة`
          : `منذ ${Math.floor(minutes / 60)} ساعة`;
      syncDisplay.textContent = `آخر مزامنة: ${timeAgo}`;
    }
  }

  async saveLastSyncTime() {
    await window.dbManager.setSetting(
      "lastSyncTime",
      this.lastSyncTime.toISOString()
    );
  }

  async loadLastSyncTime() {
    const savedTime = await window.dbManager.getSetting("lastSyncTime");
    if (savedTime) {
      this.lastSyncTime = new Date(savedTime);
    }
  }

  async getStatus() {
    const pendingOps = await window.dbManager.getPendingOperations();
    return {
      isOnline: this.isOnline,
      syncInProgress: this.syncInProgress,
      lastSyncTime: this.lastSyncTime,
      pendingOperations: pendingOps.length,
    };
  }
}

window.syncManager = new SyncManager();
