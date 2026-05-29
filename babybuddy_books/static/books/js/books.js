/**
 * books.js — Baby Buddy Books plugin
 *
 * Handles two contexts:
 *  1. Book form: title autocomplete + ISBN lookup + scanner → fills Book fields
 *  2. Reading form: searchable book select + ISBN scanner → selects/creates a Book FK
 */

(function () {
  "use strict";

  const TITLE_SEARCH_URL = "/books/title-search/";
  const ISBN_LOOKUP_URL = "/books/isbn-lookup/";
  const BOOK_SEARCH_URL = "/books/search/";
  const BOOK_QUICK_ADD_URL = "/books/quick-add/";

  // =========================================================================
  // BOOK FORM — title autocomplete + ISBN lookup + scanner
  // =========================================================================

  function initBookForm() {
    const titleInput = document.querySelector("[data-books-autocomplete='title']");
    if (!titleInput) return; // not on the book form

    const authorInput = document.getElementById("id_author");
    const isbnInput = document.querySelector("[data-books-isbn-input='true']");
    const coverInput = document.getElementById("id_cover_url");
    const suggestions = document.getElementById("books-suggestions");

    function fillBookForm(data) {
      if (titleInput && data.title) titleInput.value = data.title;
      if (authorInput && data.author) authorInput.value = data.author;
      if (isbnInput && data.isbn) isbnInput.value = data.isbn;
      if (coverInput && data.cover_url) coverInput.value = data.cover_url;
      hideSuggestions();
    }

    function hideSuggestions() {
      if (suggestions) {
        suggestions.style.display = "none";
        suggestions.innerHTML = "";
      }
    }

    function showSuggestions(results) {
      if (!suggestions) return;
      suggestions.innerHTML = "";
      if (!results.length) { suggestions.style.display = "none"; return; }
      results.forEach(function (item) {
        const a = document.createElement("a");
        a.href = "#";
        a.className = "list-group-item list-group-item-action py-2";
        const coverHtml = item.cover_url
          ? `<img src="${item.cover_url}" height="40" class="me-2 rounded" style="vertical-align:middle;">`
          : "";
        const authorHtml = item.author
          ? `<small class="text-muted d-block">${item.author}</small>`
          : "";
        a.innerHTML = `${coverHtml}<strong>${item.title}</strong>${authorHtml}`;
        a.addEventListener("click", function (e) {
          e.preventDefault();
          fillBookForm(item);
        });
        suggestions.appendChild(a);
      });
      if (titleInput) {
        const rect = titleInput.getBoundingClientRect();
        suggestions.style.top = rect.bottom + window.scrollY + "px";
        suggestions.style.left = rect.left + window.scrollX + "px";
        suggestions.style.width = rect.width + "px";
        suggestions.style.position = "absolute";
      }
      suggestions.style.display = "block";
    }

    let debounceTimer = null;
    titleInput.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      const q = titleInput.value.trim();
      if (q.length < 2) { hideSuggestions(); return; }
      debounceTimer = setTimeout(function () {
        fetch(TITLE_SEARCH_URL + "?q=" + encodeURIComponent(q))
          .then((r) => r.json())
          .then((data) => showSuggestions(data.results || []))
          .catch(() => hideSuggestions());
      }, 300);
    });

    document.addEventListener("click", function (e) {
      if (suggestions && !suggestions.contains(e.target) && e.target !== titleInput) {
        hideSuggestions();
      }
    });

    if (isbnInput) {
      isbnInput.addEventListener("change", function () {
        const isbn = isbnInput.value.trim();
        if (isbn.length < 10) return;
        fetch(ISBN_LOOKUP_URL + "?isbn=" + encodeURIComponent(isbn))
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => { if (data) fillBookForm(data); })
          .catch(() => {});
      });
    }

    initScanner({
      onIsbn: function (isbn, status) {
        if (isbnInput) isbnInput.value = isbn;
        fetch(ISBN_LOOKUP_URL + "?isbn=" + encodeURIComponent(isbn))
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data) {
              fillBookForm(data);
              status.textContent = "Found: " + data.title;
            } else {
              status.textContent = "ISBN not found in Open Library.";
            }
          })
          .catch(() => { status.textContent = "Lookup failed."; });
      },
    });
  }

  // =========================================================================
  // READING FORM — searchable book select + scanner
  // =========================================================================

  function initReadingForm() {
    const bookIdInput = document.querySelector("[data-books-book-id='true']");
    if (!bookIdInput) return; // not on the reading form

    const searchInput = document.getElementById("books-book-search");
    const suggestionsEl = document.getElementById("books-suggestions");
    const selectedDisplay = document.getElementById("books-selected-display");
    const selectedCover = document.getElementById("books-selected-cover");
    const selectedTitle = document.getElementById("books-selected-title");
    const selectedAuthor = document.getElementById("books-selected-author");
    const clearBtn = document.getElementById("books-clear-selection");
    const searchUi = document.getElementById("books-search-ui");

    function selectBook(book) {
      bookIdInput.value = book.id;
      selectedTitle.textContent = book.title;
      selectedAuthor.textContent = book.author || "";
      if (book.cover_url) {
        selectedCover.src = book.cover_url;
        selectedCover.classList.remove("d-none");
      } else {
        selectedCover.classList.add("d-none");
      }
      selectedDisplay.classList.remove("d-none");
      searchUi.classList.add("d-none");
      hideSuggestions();
    }

    function clearSelection() {
      bookIdInput.value = "";
      searchInput.value = "";
      selectedDisplay.classList.add("d-none");
      searchUi.classList.remove("d-none");
      searchInput.focus();
    }

    // Restore selection on edit
    if (window.BOOKS_INITIAL) {
      selectBook(window.BOOKS_INITIAL);
    } else if (bookIdInput.value) {
      // Pre-filled from URL ?book= param — fetch details to show
      fetch(BOOK_SEARCH_URL + "?q=")
        .then((r) => r.json())
        .then((data) => {
          const found = (data.results || []).find((b) => String(b.id) === bookIdInput.value);
          if (found) selectBook(found);
        })
        .catch(() => {});
    }

    if (clearBtn) clearBtn.addEventListener("click", clearSelection);

    function hideSuggestions() {
      if (suggestionsEl) {
        suggestionsEl.style.display = "none";
        suggestionsEl.innerHTML = "";
      }
    }

    function showBookSuggestions(results) {
      if (!suggestionsEl) return;
      suggestionsEl.innerHTML = "";
      if (!results.length) {
        // Show a "no results" hint
        const empty = document.createElement("div");
        empty.className = "list-group-item text-muted small py-2";
        empty.textContent = "No books found. Scan an ISBN to add one.";
        suggestionsEl.appendChild(empty);
      } else {
        results.forEach(function (book) {
          const a = document.createElement("a");
          a.href = "#";
          a.className = "list-group-item list-group-item-action py-2 d-flex align-items-center gap-2";
          const img = book.cover_url
            ? `<img src="${book.cover_url}" height="40" class="rounded flex-shrink-0">`
            : `<div style="width:28px;"></div>`;
          const author = book.author
            ? `<small class="text-muted d-block">${book.author}</small>`
            : "";
          a.innerHTML = `${img}<div><strong>${book.title}</strong>${author}</div>`;
          a.addEventListener("click", function (e) {
            e.preventDefault();
            selectBook(book);
          });
          suggestionsEl.appendChild(a);
        });
      }
      suggestionsEl.style.display = "block";
    }

    let debounce = null;
    if (searchInput) {
      searchInput.addEventListener("focus", function () {
        const q = searchInput.value.trim();
        fetch(BOOK_SEARCH_URL + "?q=" + encodeURIComponent(q))
          .then((r) => r.json())
          .then((data) => showBookSuggestions(data.results || []))
          .catch(() => {});
      });

      searchInput.addEventListener("input", function () {
        clearTimeout(debounce);
        const q = searchInput.value.trim();
        debounce = setTimeout(function () {
          fetch(BOOK_SEARCH_URL + "?q=" + encodeURIComponent(q))
            .then((r) => r.json())
            .then((data) => showBookSuggestions(data.results || []))
            .catch(() => hideSuggestions());
        }, 200);
      });
    }

    document.addEventListener("click", function (e) {
      if (
        suggestionsEl &&
        !suggestionsEl.contains(e.target) &&
        e.target !== searchInput
      ) {
        hideSuggestions();
      }
    });

    initScanner({
      onIsbn: function (isbn, status) {
        // First check local DB
        fetch(ISBN_LOOKUP_URL + "?isbn=" + encodeURIComponent(isbn))
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (!data) { status.textContent = "ISBN not found."; return; }
            if (data.existing_id) {
              // Already in DB — select it
              selectBook({
                id: data.existing_id,
                title: data.title,
                author: data.author,
                cover_url: data.cover_url,
              });
              status.textContent = "Selected: " + data.title;
            } else {
              // Found on Open Library — create it then select
              status.textContent = "Adding "" + data.title + "" to your library…";
              fetch(BOOK_QUICK_ADD_URL, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "X-CSRFToken": getCsrf(),
                },
                body: JSON.stringify(data),
              })
                .then((r) => r.json())
                .then((book) => {
                  selectBook(book);
                  status.textContent = "Added & selected: " + book.title;
                })
                .catch(() => { status.textContent = "Failed to add book."; });
            }
          })
          .catch(() => { status.textContent = "Lookup failed."; });
      },
    });
  }

  // =========================================================================
  // SHARED — camera scanner (ZXing)
  // =========================================================================

  function initScanner(opts) {
    const scanBtn = document.getElementById("books-scan-btn");
    const scanStop = document.getElementById("books-scan-stop");
    const container = document.getElementById("books-scanner-container");
    const video = document.getElementById("books-scanner-video");
    const status = document.getElementById("books-scan-status");

    if (!scanBtn) return;
    if (typeof ZXing === "undefined") {
      scanBtn.style.display = "none";
      return;
    }

    let codeReader = null;

    scanBtn.addEventListener("click", function () {
      container.style.display = "block";
      scanBtn.disabled = true;
      status.textContent = "Looking for camera…";

      codeReader = new ZXing.BrowserMultiFormatReader();
      codeReader
        .listVideoInputDevices()
        .then(function (devices) {
          if (!devices.length) { status.textContent = "No camera found."; return; }
          const device =
            devices.find((d) => /back|rear|environment/i.test(d.label)) ||
            devices[devices.length - 1];
          status.textContent = "Scanning — point at barcode…";
          return codeReader.decodeFromVideoDevice(
            device.deviceId,
            video,
            function (result) {
              if (result) {
                stopScanner();
                const isbn = result.getText().replace(/[^0-9X]/gi, "");
                status.textContent = "ISBN found: " + isbn + " — looking up…";
                opts.onIsbn(isbn, status);
              }
            }
          );
        })
        .catch(function (err) {
          status.textContent = "Camera error: " + err.message;
        });
    });

    function stopScanner() {
      if (codeReader) { codeReader.reset(); codeReader = null; }
      container.style.display = "none";
      scanBtn.disabled = false;
    }

    if (scanStop) scanStop.addEventListener("click", stopScanner);
  }

  // =========================================================================
  // UTIL
  // =========================================================================

  function getCsrf() {
    const el = document.querySelector("[name=csrfmiddlewaretoken]");
    return el ? el.value : "";
  }

  // =========================================================================
  // INIT
  // =========================================================================

  document.addEventListener("DOMContentLoaded", function () {
    initBookForm();
    initReadingForm();
  });
})();
