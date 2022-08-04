class MenuItem {
    constructor(path, itemName, subnavItem, next, prev) {
        this.path = path;
        this.itemName = itemName;
        this.subnavItem = subnavItem;
        this.next = next; // Next will always be the next MAIN link (never subnav)
        this.prev = prev; // Next will always be the previous MAIN link (never subnav)
    }
}

class MenuUtils {
    constructor() {
        this.subnavSelector = 'subnav';
        this.navItemSelector = 'nav__item';
        this.navItemLinkSelector = 'nav__item__link';
        this.navItemLinkContentSelector = 'nav__item__link__content';

        this.menuHeadingIds = [
            'block-guidemenuen-menu',
            'block-guidemenufi-menu',
            'block-guidemenusv-menu',
            'block-aboutopendatamenuen-menu',
            'block-aboutopendatamenufi-menu',
            'block-aboutopendatamenusv-menu',
            'block-apiprinciplesmenuen-menu',
            'block-apiprinciplesmenufi-menu',
            'block-apiprinciplesmenusv-menu',
            'block-operatingmodelmenuen-menu',
            'block-operatingmodelmenufi-menu',
            'block-operatingmodelmenusv-menu'
        ]

        this.menuLinkSelectors = [
            'block-guidemenuen',
            'block-guidemenufi',
            'block-guidemenusv',
            'block-aboutopendatamenuen',
            'block-aboutopendatamenufi',
            'block-aboutopendatamenusv',
            'block-apiprinciplesmenuen',
            'block-apiprinciplesmenufi',
            'block-apiprinciplesmenusv',
            'block-operatingmodelmenuen',
            'block-operatingmodelmenufi',
            'block-operatingmodelmenusv'
        ]

        this.menu = this.getMenu();
    }

    getMenu() {
        for (let i = 0; i < this.menuLinkSelectors.length; i++) {
            const selector = this.menuLinkSelectors[i];
            const menu = document.getElementById(selector);
            if (menu) {
                return menu;
            }
        }
        return null;
    }

    getMenuPaths() {
        let paths = [];

        const headerLink = this.getHeaderAnchorLink();
        if (headerLink) {
            paths.push(headerLink);
        }

        if (this.menu) {
            const menuItems = this.menu.getElementsByClassName(this.navItemLinkSelector);
            for (let item of menuItems) {
                const subnavElement = this.isSubnavElement(item);
                const path = item.getAttribute('href');
                const itemName = item.getElementsByClassName(this.navItemLinkContentSelector);
                const next = null;
                const prev = null;

                if (itemName.length > 0) {
                    paths.push(new MenuItem(path, itemName[0].innerText, subnavElement, next, prev));
                }
            }

            // Set the next and prev pointers so that they're always pointing at the next or previous main items in the list.
            for (let i = 0; i < paths.length; i++) {
                if (i === 0) {
                    paths[i].next = this.getNextMainElementIndex(i, paths);
                }

                if (i === paths.length - 1) {
                    paths[i].prev = this.getPreviousMainElementIndex(i, paths);
                }

                if (i > 0 && i < paths.length) {
                    paths[i].prev = this.getPreviousMainElementIndex(i, paths);
                    paths[i].next = this.getNextMainElementIndex(i, paths);
                }
            }
        }
        return paths;
    }

    getPreviousMainElementIndex(index, paths) {
        const currentItem = paths[index];
        for (let i = index - 1; i >= 0; i--) {
            if (paths[i].subnavItem === false) {
                // If currentItem is a subNavitem, then the first previous main item that we encounter is the parent item.
                // So we need to get the previous item from the parent in order for this to be correct.
                if (currentItem.subnavItem === true && i > 0) {
                    return i - 1;
                }
                return i;
            }
        }
    }

    getNextMainElementIndex(index, paths) {
        for (let i = index + 1; i < paths.length; i++) {
            if (paths[i].subnavItem === false) {
                return i;
            }
        }
    }

    isSubnavElement(item) {
        const subnavClass = '.' + this.subnavSelector;
        return item.closest(subnavClass) !== null;
    }

    getHeaderAnchorLink() {
        /**
         * Get thhe header link since the header is a separate element and might contain a link.
         * This should also be the first page of the guide page where the users lands when clicking
         * the menu.
         */
        for (const path of this.menuHeadingIds) {
            const link = document.getElementById(path);
            if (link) {
                const subnavElement = this.isSubnavElement(link);
                let linkAnchors = link.getElementsByTagName('a');
                if (linkAnchors.length > 0) {
                    let href = linkAnchors[0].getAttribute('href');
                    return new MenuItem(href, link.innerText, subnavElement);
                }
            }
        }

        return null;
    }
}

class GuidePageView {
    constructor(menuUtils) {
        this.currentPath = window.location.pathname;
        this.nextBtn = document.getElementById('next-page-btn');
        this.prevBtn = document.getElementById('previous-page-btn');
        this.paths = menuUtils.getMenuPaths();
        this.arrowBoxTitleSelector = document.getElementById('arrow-box-title');
        this.arrowBoxSelector = document.getElementById('js-arrow-box');

        this.setAnchorLinks();
        this.setArrowBoxTitle();
    }

    setArrowBoxTitle() {
        if (this.paths.length <= 0) {
            return;
        }

        // First item in the list should be the header which will be displayed in the Arrowbox.
        let headerPathName = this.paths[0].itemName;
        if (headerPathName) {
            this.arrowBoxTitleSelector.innerText = headerPathName;
        }
    }

    setAnchorLinks() {
        if (this.paths.length <= 0) {
            return;
        }

        const currentPageIndex = this.getIndexOfCurrentPage();

        this.setNextAnchorLink(currentPageIndex);
        this.setPrevAnchorLink(currentPageIndex);
    }

    setNextAnchorLink(currentPageIndex) {
        const currentElement = this.paths[currentPageIndex];
        if (currentElement.next === undefined) {
            this.nextBtn.style.display = 'none';
            return;
        }

        const innerChevron = '<i class="far fa-chevron-right"></i>';
        const nextMainElement = this.paths[currentElement.next];

        this.nextBtn.innerHTML = nextMainElement.itemName + innerChevron;
        this.nextBtn.href = nextMainElement.path;
    }

    setPrevAnchorLink(currentPageIndex) {
        const currentElement = this.paths[currentPageIndex];
        if (currentElement.prev === undefined) {
            this.prevBtn.style.display = 'none';
            return;
        }

        const innerChevron = '<i class="far fa-chevron-left"></i>';
        const prevMainElement = this.paths[currentElement.prev];

        this.prevBtn.innerHTML = innerChevron + prevMainElement.itemName;
        this.prevBtn.href = prevMainElement.path;
    }

    getIndexOfCurrentPage() {
        return this.paths.map(function (e) { return e.path; }).indexOf(this.currentPath);
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    new GuidePageView(new MenuUtils());
});
