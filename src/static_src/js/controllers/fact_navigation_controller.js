import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["older", "newer"];

    older() {
        if (this.hasOlderTarget) this.olderTarget.click();
    }

    newer() {
        if (this.hasNewerTarget) this.newerTarget.click();
    }
}
