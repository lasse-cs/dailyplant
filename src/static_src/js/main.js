import "../css/style.css";
import "htmx.org";

import { Application } from "@hotwired/stimulus";
import AccordionController from "./controllers/accordion_controller";
import ClipboardController from "./controllers/clipboard_controller";
import SearchController from "./controllers/search_controller";
import TabController from "./controllers/tab_controller";
import TocController from "./controllers/toc_controller";

export const application = Application.start();

application.register("accordion", AccordionController);
application.register("clipboard", ClipboardController);
application.register("search", SearchController);
application.register("toc", TocController);
application.register("tab", TabController);
