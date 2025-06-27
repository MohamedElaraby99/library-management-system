// معالج العمليات غير المتصلة
class OfflineHandler {
  constructor() {
    this.isInitialized = false;
    this.init();
  }

  async init() {
    // انتظار تحميل مديري قاعدة البيانات والمزامنة
    await this.waitForManagers();

    // تحديث واجهة المستخدم
    this.enhanceUI();

    // تحميل البيانات المحلية في الصفحات المناسبة
    this.loadOfflineData();

    this.isInitialized = true;
    console.log("Offline handler initialized");
  }

  async waitForManagers() {
    let attempts = 0;
    while ((!window.dbManager || !window.syncManager) && attempts < 10) {
      await new Promise((resolve) => setTimeout(resolve, 100));
      attempts++;
    }

    if (!window.dbManager || !window.syncManager) {
      throw new Error("Failed to initialize offline managers");
    }
  }

  enhanceUI() {
    this.addOfflineStatusBar();
    this.enhanceProductSearch();
    this.enhanceCustomerSearch();
    this.enhanceSalesForm();
  }

  addOfflineStatusBar() {
    // إنشاء شريط الحالة
    const statusBar = document.createElement("div");
    statusBar.className = "offline-status-bar";
    statusBar.innerHTML = `
            <div class="container-fluid">
                <div class="row align-items-center justify-content-between">
                    <div class="col-auto">
                        <span id="network-status" class="network-status offline">
                            <i class="bi bi-wifi-off"></i>
                            غير متصل
                        </span>
                    </div>
                    <div class="col-auto">
                        <span id="sync-indicator" class="sync-indicator">
                            <i class="bi bi-arrow-repeat"></i>
                            مزامنة
                        </span>
                    </div>
                    <div class="col-auto">
                        <span id="last-sync-time" class="last-sync-time">
                            آخر مزامنة: لم تتم
                        </span>
                    </div>
                    <div class="col-auto">
                        <button id="manual-sync-btn" class="btn btn-outline-primary btn-sm" onclick="window.syncManager.performSync()">
                            <i class="bi bi-arrow-clockwise"></i>
                            مزامنة
                        </button>
                    </div>
                    <div class="col-auto">
                        <button id="hide-status-bar" class="btn btn-outline-secondary btn-sm d-md-none" onclick="window.offlineHandler.toggleStatusBar()">
                            <i class="bi bi-chevron-up"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

    // إدراج شريط الحالة
    document.body.insertBefore(statusBar, document.body.firstChild);

    // إضافة وظائف التحكم في الشريط
    this.setupStatusBarControls();
  }

  // إضافة وظائف التحكم في شريط الحالة
  setupStatusBarControls() {
    let lastScrollY = window.scrollY;
    let isStatusBarVisible = true;
    let scrollTimeout;

    // مراقبة التمرير للموبايل
    if (window.innerWidth <= 768) {
      window.addEventListener("scroll", () => {
        clearTimeout(scrollTimeout);

        scrollTimeout = setTimeout(() => {
          const currentScrollY = window.scrollY;
          const statusBar = document.querySelector(".offline-status-bar");

          if (currentScrollY > lastScrollY && currentScrollY > 100) {
            // التمرير للأسفل - إخفاء الشريط
            if (isStatusBarVisible) {
              statusBar.classList.add("mobile-hidden");
              isStatusBarVisible = false;
            }
          } else if (currentScrollY < lastScrollY || currentScrollY <= 50) {
            // التمرير للأعلى أو في الأعلى - إظهار الشريط
            if (!isStatusBarVisible) {
              statusBar.classList.remove("mobile-hidden");
              isStatusBarVisible = true;
            }
          }

          lastScrollY = currentScrollY;
        }, 100);
      });
    }
  }

  // وظيفة التبديل بين إظهار/إخفاء الشريط
  toggleStatusBar() {
    const statusBar = document.querySelector(".offline-status-bar");
    const hideBtn = document.querySelector("#hide-status-bar");

    if (statusBar.classList.contains("hidden")) {
      statusBar.classList.remove("hidden");
      hideBtn.innerHTML = '<i class="bi bi-chevron-up"></i>';
    } else {
      statusBar.classList.add("hidden");
      hideBtn.innerHTML = '<i class="bi bi-chevron-down"></i>';
    }
  }

  enhanceProductSearch() {
    const productSearchInput = document.querySelector("#productSearch");
    if (productSearchInput) {
      productSearchInput.addEventListener("input", async (e) => {
        const searchTerm = e.target.value.trim();
        if (searchTerm.length >= 2) {
          await this.searchProductsOffline(searchTerm);
        }
      });
    }
  }

  async searchProductsOffline(searchTerm) {
    try {
      const products = await window.syncManager.getProductsLocal({
        search: searchTerm,
      });

      this.displayProductResults(products);
    } catch (error) {
      console.error("Error searching products offline:", error);
    }
  }

  displayProductResults(products) {
    const resultsContainer = document.querySelector("#productResults");
    if (!resultsContainer) return;

    resultsContainer.innerHTML = "";

    products.forEach((product) => {
      const productDiv = document.createElement("div");
      productDiv.className = "product-item border rounded p-3 mb-2";
      productDiv.innerHTML = `
                <div class="row align-items-center">
                    <div class="col">
                        <h6 class="mb-1">${product.name_ar}</h6>
                        <small class="text-muted">الكمية: ${
                          product.stock_quantity
                        }</small>
                    </div>
                    <div class="col-auto">
                        <span class="badge ${
                          product.stock_quantity > 0
                            ? "bg-success"
                            : "bg-danger"
                        }">
                            ${product.stock_quantity > 0 ? "متوفر" : "نفد"}
                        </span>
                    </div>
                    <div class="col-auto">
                        <strong>${product.retail_price} ج.م</strong>
                    </div>
                </div>
            `;

      productDiv.addEventListener("click", () => {
        this.addProductToCart(product);
      });

      resultsContainer.appendChild(productDiv);
    });
  }

  enhanceCustomerSearch() {
    const customerSearchInput = document.querySelector("#customerSearch");
    if (customerSearchInput) {
      customerSearchInput.addEventListener("input", async (e) => {
        const searchTerm = e.target.value.trim();
        if (searchTerm.length >= 2) {
          await this.searchCustomersOffline(searchTerm);
        }
      });
    }
  }

  async searchCustomersOffline(searchTerm) {
    try {
      const customers = await window.syncManager.getCustomersLocal(searchTerm);
      this.displayCustomerResults(customers);
    } catch (error) {
      console.error("Error searching customers offline:", error);
    }
  }

  displayCustomerResults(customers) {
    const dropdown = document.querySelector("#customerDropdown");
    if (!dropdown) return;

    dropdown.innerHTML = "";

    customers.forEach((customer) => {
      const option = document.createElement("a");
      option.className = "dropdown-item";
      option.href = "#";
      option.innerHTML = `
                <div>
                    <strong>${customer.name}</strong>
                    ${
                      customer.phone
                        ? `<br><small class="text-muted">${customer.phone}</small>`
                        : ""
                    }
                </div>
            `;

      option.addEventListener("click", (e) => {
        e.preventDefault();
        this.selectCustomer(customer);
      });

      dropdown.appendChild(option);
    });

    dropdown.style.display = customers.length > 0 ? "block" : "none";
  }

  enhanceSalesForm() {
    const salesForm = document.querySelector("#salesForm");
    if (salesForm) {
      salesForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await this.processSaleOffline();
      });
    }
  }

  async processSaleOffline() {
    try {
      const saleData = this.collectSaleData();

      if (!saleData.items || saleData.items.length === 0) {
        this.showError("يرجى إضافة منتجات للبيع");
        return;
      }

      // حفظ البيع محلياً
      const saleId = await window.syncManager.saveSaleLocal(saleData);

      this.showSuccess(`تم حفظ البيع رقم ${saleId} محلياً`);
      this.clearSaleForm();

      // محاولة المزامنة إذا كان متصلاً
      if (window.syncManager.isOnline) {
        window.syncManager.showNotification("جاري رفع البيع للخادم...", "info");
      } else {
        window.syncManager.showNotification(
          "سيتم رفع البيع عند توفر الاتصال",
          "warning"
        );
      }
    } catch (error) {
      console.error("Error processing sale offline:", error);
      this.showError("حدث خطأ أثناء حفظ البيع");
    }
  }

  collectSaleData() {
    // جمع بيانات البيع من النموذج
    const customerId = document.querySelector("#selectedCustomerId")?.value;
    const paymentStatus =
      document.querySelector("#paymentStatus")?.value || "paid";
    const paymentType = document.querySelector("#paymentType")?.value || "cash";
    const notes = document.querySelector("#saleNotes")?.value || "";

    // جمع عناصر البيع من السلة
    const items = this.collectCartItems();

    return {
      customer_id: customerId || null,
      items: items,
      payment_status: paymentStatus,
      payment_type: paymentType,
      notes: notes,
      sale_date: new Date().toISOString(),
    };
  }

  collectCartItems() {
    const cartItems = document.querySelectorAll(".cart-item");
    const items = [];

    cartItems.forEach((item) => {
      const productId = item.dataset.productId;
      const quantity = parseFloat(
        item.querySelector(".quantity-input")?.value || 0
      );
      const unitPrice = parseFloat(item.dataset.unitPrice || 0);

      if (productId && quantity > 0) {
        items.push({
          product_id: parseInt(productId),
          quantity: quantity,
          unit_price: unitPrice,
          total_price: quantity * unitPrice,
        });
      }
    });

    return items;
  }

  addProductToCart(product) {
    // إضافة منتج للسلة
    const cartContainer = document.querySelector("#cartItems");
    if (!cartContainer) return;

    const existingItem = cartContainer.querySelector(
      `[data-product-id="${product.id}"]`
    );

    if (existingItem) {
      // زيادة الكمية للمنتج الموجود
      const quantityInput = existingItem.querySelector(".quantity-input");
      quantityInput.value = parseInt(quantityInput.value) + 1;
      this.updateCartItemTotal(existingItem);
    } else {
      // إضافة منتج جديد
      const cartItem = this.createCartItem(product);
      cartContainer.appendChild(cartItem);
    }

    this.updateCartTotal();
  }

  createCartItem(product) {
    const div = document.createElement("div");
    div.className = "cart-item border-bottom py-2";
    div.dataset.productId = product.id;
    div.dataset.unitPrice = product.retail_price;

    div.innerHTML = `
            <div class="row align-items-center">
                <div class="col">
                    <h6 class="mb-0">${product.name_ar}</h6>
                    <small class="text-muted">${product.retail_price} ج.م</small>
                </div>
                <div class="col-auto">
                    <input type="number" class="form-control form-control-sm quantity-input" 
                           value="1" min="1" max="${product.stock_quantity}" style="width: 70px;">
                </div>
                <div class="col-auto">
                    <span class="item-total">${product.retail_price}</span> ج.م
                </div>
                <div class="col-auto">
                    <button class="btn btn-sm btn-outline-danger remove-item">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;

    // إضافة مستمعي الأحداث
    const quantityInput = div.querySelector(".quantity-input");
    quantityInput.addEventListener("change", () =>
      this.updateCartItemTotal(div)
    );

    const removeBtn = div.querySelector(".remove-item");
    removeBtn.addEventListener("click", () => {
      div.remove();
      this.updateCartTotal();
    });

    return div;
  }

  updateCartItemTotal(cartItem) {
    const quantity = parseFloat(
      cartItem.querySelector(".quantity-input").value
    );
    const unitPrice = parseFloat(cartItem.dataset.unitPrice);
    const total = quantity * unitPrice;

    cartItem.querySelector(".item-total").textContent = total.toFixed(2);
    this.updateCartTotal();
  }

  updateCartTotal() {
    const cartItems = document.querySelectorAll(".cart-item");
    let total = 0;

    cartItems.forEach((item) => {
      const itemTotal = parseFloat(
        item.querySelector(".item-total").textContent
      );
      total += itemTotal;
    });

    const totalDisplay = document.querySelector("#cartTotal");
    if (totalDisplay) {
      totalDisplay.textContent = `${total.toFixed(2)} ج.م`;
    }

    // تحديث عدد العناصر
    const countBadge = document.querySelector(".cart-count-badge");
    if (countBadge) {
      countBadge.textContent = cartItems.length;
    }
  }

  selectCustomer(customer) {
    const searchInput = document.querySelector("#customerSearch");
    const customerIdInput = document.querySelector("#selectedCustomerId");
    const dropdown = document.querySelector("#customerDropdown");

    if (searchInput) searchInput.value = customer.name;
    if (customerIdInput) customerIdInput.value = customer.id;
    if (dropdown) dropdown.style.display = "none";
  }

  clearSaleForm() {
    const cartContainer = document.querySelector("#cartItems");
    if (cartContainer) cartContainer.innerHTML = "";

    const customerSearch = document.querySelector("#customerSearch");
    if (customerSearch) customerSearch.value = "";

    const customerIdInput = document.querySelector("#selectedCustomerId");
    if (customerIdInput) customerIdInput.value = "";

    this.updateCartTotal();
  }

  showSuccess(message) {
    window.syncManager.showNotification(message, "success");
  }

  showError(message) {
    window.syncManager.showNotification(message, "error");
  }

  async loadOfflineData() {
    // تحميل البيانات المحلية حسب الصفحة الحالية
    const currentPage = window.location.pathname;

    if (currentPage.includes("/sales/new")) {
      await this.preloadSalesData();
    } else if (currentPage.includes("/products")) {
      await this.preloadProductsData();
    }
  }

  async preloadSalesData() {
    try {
      // تحميل المنتجات والعملاء مسبقاً
      await Promise.all([
        window.syncManager.getProductsLocal(),
        window.syncManager.getCustomersLocal(),
        window.syncManager.getCategoriesLocal(),
      ]);

      console.log("Sales data preloaded successfully");
    } catch (error) {
      console.error("Error preloading sales data:", error);
    }
  }

  async preloadProductsData() {
    try {
      await window.syncManager.getProductsLocal();
      console.log("Products data preloaded successfully");
    } catch (error) {
      console.error("Error preloading products data:", error);
    }
  }
}

// تهيئة معالج العمليات غير المتصلة
document.addEventListener("DOMContentLoaded", () => {
  window.offlineHandler = new OfflineHandler();
});
