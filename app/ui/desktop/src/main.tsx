import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./applicants.css";
import "./applications.css";
import "./screening.css";
import "./interviews.css";
import "./overview.css";
import "./screening-reference.css";
import "./municipal-theme.css";
import "./screening-match.css";

document.documentElement.dataset.theme = localStorage.getItem("iskolar-theme") === "dark" ? "dark" : "light";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode><App /></React.StrictMode>,
);
