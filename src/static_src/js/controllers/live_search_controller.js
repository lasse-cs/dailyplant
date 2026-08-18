import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["status", "announcement"];

    announce() {
        if (!this.hasAnnouncementTarget) {
            return;
        }

        this.statusTarget.textContent =
            this.announcementTarget.content.textContent.trim();
        this.announcementTarget.remove();
    }
}
