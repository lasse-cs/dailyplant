import "../css/style.css";
import "htmx.org";

import { Application } from "@hotwired/stimulus";
import ClipboardController from "./controllers/clipboard_controller";
import SearchController from "./controllers/search_controller";

export const application = Application.start();

application.register("clipboard", ClipboardController);
application.register("search", SearchController);
