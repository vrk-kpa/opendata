class MenuItem {
    constructor(path, itemName) {
        this.path = path;
        this.itemName = itemName;
    }
}

class CycleGuideMenuItem {
    constructor() {
        this.menu = this.getMenu();
        this.paths = this.getMenuPaths();

        this.currentPath = window.location.pathname;
        this.nextBtn = document.getElementById('next-page-btn');
        this.prevBtn = document.getElementById('previous-page-btn');

        this.setBtnTexts();
    }

    attachBtnEvents() {
        this.nextBtn.addEventListener('click', event  => { this.moveToNextPage() });
        this.prevBtn.addEventListener('click', event  => { this.moveToPreviousPage() });
    }

    setBtnTexts() {
        const currentPageIndex = this.getIndexOfCurrentPage();
        this.setNextBtnText(currentPageIndex);
        this.setPrevBtnText(currentPageIndex);
    }

    setNextBtnText(currentPageIndex) {
        const nextString = this.nextBtn.innerHTML;

        if (this.isFrontpage()) {
            this.nextBtn.innerHTML = nextString + ': ' + this.paths[0].itemName;
        } else {
            if (currentPageIndex < this.paths.length - 1) {
                let nextPageIndex = currentPageIndex + 1;
                this.nextBtn.innerHTML = nextString + ': ' + this.paths[nextPageIndex].itemName;
            }
            else {
                this.nextBtn.disabled = true;
            }
        }
    }

    setPrevBtnText(currentPageIndex) {
        const prevString = this.prevBtn.innerHTML;

        if (this.isFrontpage() || currentPageIndex == 0) {
            this.prevBtn.disabled = true;
        } else {
            if (currentPageIndex > 0) {
                let prevPageIndex = currentPageIndex - 1;
                this.prevBtn.innerHTML = prevString + ': ' + this.paths[prevPageIndex].itemName;
            }
        }
    }

    getMenu() {
        const menuLinkSelectors = [
            'block-guidemenuen',
            'block-guidemenufi',
            'block-guidemenusv'
        ]

        for (let i = 0; i < menuLinkSelectors.length; i++) {
            const selector = menuLinkSelectors[i];
            const menu = document.getElementById(selector);
            if (menu) {
                return menu;
            }
        }

        return null;
    }

    getMenuPaths() {
        const aTags = this.menu.getElementsByTagName('a');
        let paths = [];

        for (const tag of aTags) {
            let path = tag.getAttribute('href');
            let itemName = tag.getElementsByClassName('link-content');
            paths.push(new MenuItem(path, itemName[0].innerText));
        }

        return paths
    }

    getIndexOfCurrentPage() {
        return this.paths.map(function (e) { return e.path; }).indexOf(this.currentPath);
    }

    moveToNextPage() {
        if (this.paths === []) { return; }

        if (this.isFrontpage()) {
            window.location = this.paths[0].path;
        } else {
            const index = this.getIndexOfCurrentPage();
            const nextPage = index + 1;
            if (nextPage < this.paths.length) {
                window.location = this.paths[nextPage].path;
            }
        }
    }

    moveToPreviousPage() {
        if (this.paths === []) { return; }

        if (this.isFrontpage()) {
            return;
        } else {
            const index = this.getIndexOfCurrentPage();
            const prevPage = index - 1;
            if (prevPage >= 0) {
                window.location = this.paths[prevPage].path;
            }
        }
    }

    isFrontpage() {
        const frontpagePaths = [
            '/fi/opas/oppaan-etusivu',
            '/sv/guide/guide-startsidan',
            '/en/guide/guide-frontpage'
        ]

        for (const path of frontpagePaths) {
            if (path === this.currentPath) {
                return true;
            }
        }

        return false;
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    const cycle = new CycleGuideMenuItem();
    cycle.attachBtnEvents();
});
