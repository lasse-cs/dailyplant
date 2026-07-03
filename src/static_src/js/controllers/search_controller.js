import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["dialog", "shortcut"];

    connect() {
        if (this.isMac()) {
            this.shortcutTarget.textContent = "⌘ K";
        }
    }

    isMac() {
        const platform = navigator.userAgentData?.platform || navigator.platform || "";

        return platform.toLowerCase().includes("mac");
    }

    open() {
        if (!this.dialogTarget.open) {
            this.dialogTarget.showModal();
        }
    }

    openForKey(event) {
        if (!(event instanceof KeyboardEvent)) {
            return;
        }
        event.preventDefault();
        this.open();
    }

    close() {
        this.dialogTarget.close();
    }

    dialogClick(event) {
        if (event.target === this.dialogTarget) {
            this.close();
        }
    }
}
