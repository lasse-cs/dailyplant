import "../css/style.css";

import { Application } from "@hotwired/stimulus";
import ClipboardController from "./controllers/clipboard_controller";

export const application = Application.start();

application.register("clipboard", ClipboardController);
