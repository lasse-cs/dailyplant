import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["tablist"];
    static classes = ["hidden"];

    connect() {
        this.tabs = [];
        this.panels = [];
        this.tablistTarget.querySelectorAll("[role=tab]").forEach((tab) => {
            this.tabs.push(tab);
            this.panels.push(
                document.getElementById(tab.getAttribute("aria-controls")),
            );
        });
        this.selectTab(this.tabs[0]);
    }

    select({ currentTarget }) {
        this.selectTab(currentTarget);
    }

    selectTab(tabToSelect) {
        this.tabs.forEach((tab, index) => {
            if (tab === tabToSelect) {
                tab.setAttribute("aria-selected", "true");
                tab.removeAttribute("tabindex");
                this.panels[index].classList.remove(this.hiddenClass);
            } else {
                tab.setAttribute("aria-selected", "false");
                tab.tabIndex = -1;
                this.panels[index].classList.add(this.hiddenClass);
            }
        });
    }

    move(event) {
        let tabToMoveTo = null;
        switch (event.key) {
            case "ArrowLeft": {
                const index = this.tabs.indexOf(event.currentTarget);
                tabToMoveTo =
                    this.tabs[
                        (index - 1 + this.tabs.length) % this.tabs.length
                    ];
                break;
            }
            case "ArrowRight": {
                const index = this.tabs.indexOf(event.currentTarget);
                tabToMoveTo = this.tabs[(index + 1) % this.tabs.length];
                break;
            }
            case "Home": {
                tabToMoveTo = this.tabs[0];
                break;
            }
            case "End": {
                tabToMoveTo = this.tabs[this.tabs.length - 1];
                break;
            }
            default:
                break;
        }

        if (!tabToMoveTo) {
            return;
        }

        event.stopPropagation();
        event.preventDefault();
        tabToMoveTo.focus();
    }
}
