let flipbook = null;
let zoom = null;

$(document).ready(function () {
    const $flipbook = $('#flipbook');

    const PAGE_WIDTH = 1275;
    const PAGE_HEIGHT = 1650;
    const BOOK_WIDTH = PAGE_WIDTH * 2;   // 2550
    const BOOK_HEIGHT = PAGE_HEIGHT;     // 1650
    const BOOK_RATIO = BOOK_WIDTH / BOOK_HEIGHT;
	
	flipbook = $('#flipbook');
	
    $flipbook.turn({
        width: BOOK_WIDTH,
        height: BOOK_HEIGHT,
        autoCenter: true,
        display: 'double',
        acceleration: true,
        gradients: true,
        elevation: 50
    });

    window.nextPage = function () {
        $flipbook.turn('next');
    };

    window.prevPage = function () {
        $flipbook.turn('previous');
    };

    function resizeFlipbook() {
        const $container = $('.book');
		const $zoomContainer = $('#zoom-container');

        const containerWidth = $container.width();
        const containerHeight = $container.height();

        let newWidth = containerWidth;
        let newHeight = newWidth / BOOK_RATIO;

        if (newHeight > containerHeight) {
            newHeight = containerHeight;
            newWidth = newHeight * BOOK_RATIO;
        }

        $flipbook.turn('size', Math.floor(newWidth), Math.floor(newHeight));
		
		$flipbook.css({
			left: (containerWidth - newWidth) / 2 + 'px',
			top: (containerHeight - newHeight) / 2 + 'px'
		});
    }

    resizeFlipbook();

    let resizeTimeout;
    $(window).on('resize', function () {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function () {
            resizeFlipbook();
        }, 100);
    });
	
	// Zoom
	const container = $('#zoom-container');

    zoom = container.zoom({
        flipbook: $('#flipbook'),

        max: function () {
            return 2.5; // zoom level
        },

        when: {
            tap: function (event) {

                // Ignore clicks on links
                if ($(event.target).closest('a').length) return;

                const $this = $(this);

				if ($this.zoom('value') === 1) {
					$this.zoom('zoomIn', event);
					container.addClass('zoomed');
				} else {
					$this.zoom('zoomOut');
					container.removeClass('zoomed');
				}
            },

            doubleTap: function (event) {
                // optional: same as single tap
            },

            resize: function (event, scale, page, pageElement) {
                if (scale === 1) {
                    container.removeClass('zoomed');
                }
            }
        }
    });
	
	window.closeZoom = function () {
		const container = $('#zoom-container');

		container.zoom('zoomOut');
		container.removeClass('zoomed');
	};
	
	// Thumbnail navigation
	let thumbOffset = 0;
	const thumbWidth = 85; // 75 + margin

	window.scrollThumbs = function (direction) {
		const track = document.querySelector('.thumb-track');
		const viewport = document.querySelector('.thumb-viewport');

		const visibleWidth = viewport.offsetWidth;
		const maxOffset = track.scrollWidth - visibleWidth;

		thumbOffset += direction * visibleWidth * 0.8;

		if (thumbOffset < 0) thumbOffset = 0;
		if (thumbOffset > maxOffset) thumbOffset = maxOffset;

		track.style.transform = `translateX(-${thumbOffset}px)`;
	}

	/* GO TO PAGE */
	window.goToPage = function (page) {
		$('#flipbook').turn('page', page);
	}

	/* SHOW / HIDE BAR */
	const toggle = document.querySelector('.thumb-toggle');
	const bar = document.querySelector('.thumb-bar');

	toggle.addEventListener('mouseenter', () => {
		bar.classList.add('active');
	});

	bar.addEventListener('mouseleave', () => {
		bar.classList.remove('active');
	});
	
	// archive
	const archiveToggle = document.querySelector('.archive-toggle');
	const archiveMenu = document.querySelector('.archive-menu');

	if (archiveToggle && archiveMenu) {
		archiveToggle.addEventListener('mouseenter', () => {
			archiveMenu.classList.add('active');
		});

		archiveMenu.addEventListener('mouseleave', () => {
			archiveMenu.classList.remove('active');
		});
	}
	
	const archiveModal = document.querySelector('.archive-modal');
	const archiveClose = document.querySelector('.archive-close');

	/* OPEN MODAL */
	const archiveContent = document.querySelector('.archive-content');

	if (archiveContent) {
		archiveContent.addEventListener('click', () => {
			archiveModal.classList.add('active');
			loadArchive();
		});
	}

	/* CLOSE BUTTON */
	if (archiveClose) {
		archiveClose.addEventListener('click', () => {
			archiveModal.classList.remove('active');
		});
	}

	/* CLICK OUTSIDE TO CLOSE */
	archiveModal.addEventListener('click', (e) => {
		if (e.target === archiveModal) {
			archiveModal.classList.remove('active');
		}
	});

	/* ESC KEY CLOSE */
	document.addEventListener('keydown', (e) => {
		if (e.key === 'Escape') {
			archiveModal.classList.remove('active');
		}
	});
	
	function loadArchive() {
		fetch('../library.json')
			.then(res => res.json())
			.then(data => {
				const grid = document.querySelector('.archive-grid');
				grid.innerHTML = '';

				const items = data.menu.item[0].item;

				items.forEach(item => {
					if (!item._sPublished) return;

					const div = document.createElement('div');
					div.className = 'archive-item';

					div.innerHTML = `
						<img src="${item._sCover}">
						<div class="archive-item-title">${item._sTitle}</div>
					`;

					div.onclick = () => {
						window.location.href = item._sURL;
					};

					grid.appendChild(div);
				});
			})
			.catch(err => {
				console.error('Error loading archive:', err);
			});
	}
	
	function printPages(pageNumbers) {
		const pages = window.FLIPBOOK_PAGES || [];
		const title = window.FLIPBOOK_TITLE || 'Flipbook';

		console.log('[Print] Requested pages:', pageNumbers);
		console.log('[Print] Available page images:', pages);

		if (!pages.length) {
			console.error('[Print] No page images were provided.');
			alert('The page images could not be loaded for printing.');
			return;
		}

		const validPages = pageNumbers
			.map(pageNumber => ({
				pageNumber,
				src: pages[pageNumber - 1]
			}))
			.filter(page => page.src);

		if (!validPages.length) {
			console.error('[Print] None of the requested pages were valid.');
			alert('No valid pages were found to print.');
			return;
		}

		// Remove an older print frame if one remains.
		const oldFrame = document.getElementById('flipbook-print-frame');

		if (oldFrame) {
			oldFrame.remove();
		}

		const iframe = document.createElement('iframe');

		iframe.id = 'flipbook-print-frame';
		iframe.setAttribute('title', 'Print preview');

		Object.assign(iframe.style, {
			position: 'fixed',
			right: '0',
			bottom: '0',
			width: '1px',
			height: '1px',
			border: '0',
			opacity: '0',
			pointerEvents: 'none'
		});

		document.body.appendChild(iframe);

		const printWindow = iframe.contentWindow;
		const printDocument = iframe.contentDocument || printWindow.document;

		if (!printWindow || !printDocument) {
			console.error('[Print] Could not access the print iframe.');
			iframe.remove();
			alert('The print view could not be created.');
			return;
		}

		printDocument.open();
		printDocument.write(`
			<!DOCTYPE html>
			<html>
			<head>
				<meta charset="UTF-8">
				<title></title>

				<style>
					@page {
						margin: 0.25in;
					}

					html,
					body {
						margin: 0;
						padding: 0;
						background: #fff;
					}

					.print-page {
						width: 100%;
						height: calc(100vh - 0.5in);
						display: flex;
						align-items: center;
						justify-content: center;
						page-break-after: always;
						break-after: page;
						overflow: hidden;
					}

					.print-page:last-child {
						page-break-after: auto;
						break-after: auto;
					}

					.print-page img {
						display: block;
						width: auto;
						height: auto;
						max-width: 100%;
						max-height: 100%;
						object-fit: contain;
					}
				</style>
			</head>

			<body></body>
			</html>
		`);
		printDocument.close();

		printDocument.title = `${title} - Print`;

		const imagePromises = validPages.map(page => {
			return new Promise(resolve => {
				const pageContainer = printDocument.createElement('div');
				const image = printDocument.createElement('img');

				pageContainer.className = 'print-page';

				image.alt = `Page ${page.pageNumber}`;
				image.src = new URL(page.src, window.location.href).href;

				image.addEventListener('load', function () {
					console.log(
						`[Print] Loaded page ${page.pageNumber}:`,
						image.src
					);
					resolve();
				});

				image.addEventListener('error', function () {
					console.error(
						`[Print] Failed to load page ${page.pageNumber}:`,
						image.src
					);
					resolve();
				});

				pageContainer.appendChild(image);
				printDocument.body.appendChild(pageContainer);
			});
		});

		Promise.all(imagePromises).then(function () {
			console.log('[Print] Images finished loading. Opening print dialog.');

			printWindow.focus();
			printWindow.print();

			const cleanup = function () {
				window.setTimeout(function () {
					iframe.remove();
				}, 500);
			};

			if ('onafterprint' in printWindow) {
				printWindow.onafterprint = cleanup;
			} else {
				window.setTimeout(cleanup, 3000);
			}
		});
	}

	window.printAllPages = function () {
		const pages = window.FLIPBOOK_PAGES || [];
		const pageNumbers = pages.map((_, index) => index + 1);

		printPages(pageNumbers);
	};

	window.printCurrentPages = function () {
		const $flipbook = $('#flipbook');

		const currentPage = $flipbook.turn('page');
		const totalPages = $flipbook.turn('pages');

		let pageNumbers = [];

		if (currentPage === 1 || currentPage === totalPages) {
			pageNumbers = [currentPage];
		} else if (currentPage % 2 === 0) {
			pageNumbers = [currentPage, currentPage + 1];
		} else {
			pageNumbers = [currentPage - 1, currentPage];
		}

		pageNumbers = pageNumbers.filter(p => p >= 1 && p <= totalPages);

		printPages(pageNumbers);
	};
	
});