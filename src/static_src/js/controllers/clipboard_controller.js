import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static classes = ["copied"];

    static values = {
        resetDelay: { type: Number, default: 2000 },
        text: String,
    };

    disconnect() {
        clearTimeout(this.resetTimeout);
    }

    async copy(event) {
        event.preventDefault();
        try {
            await navigator.clipboard.writeText(this.textValue);

            this.element.classList.add(...this.copiedClasses);
            clearTimeout(this.resetTimeout);
            this.resetTimeout = setTimeout(() => {
                this.element.classList.remove(...this.copiedClasses);
            }, this.resetDelayValue);
        } catch {
            return;
        }
    }
}
