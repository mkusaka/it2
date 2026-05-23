import { readFile } from "node:fs/promises";
import { basename } from "node:path";

const sarifPath = process.argv[2];

if (!sarifPath) {
  console.error("Usage: node check-codeql-sarif.mjs <sarif-file>");
  process.exit(2);
}

const sarif = JSON.parse(await readFile(sarifPath, "utf8"));
const findings = [];

for (const run of sarif.runs ?? []) {
  const driverRules = run.tool?.driver?.rules ?? [];
  const rules = new Map(driverRules.map((rule) => [rule.id, rule]));

  for (const result of run.results ?? []) {
    if (isAcceptedSuppression(result)) {
      continue;
    }

    const location = result.locations?.[0]?.physicalLocation;
    const region = location?.region ?? {};
    const uri = location?.artifactLocation?.uri ?? basename(sarifPath);
    const rule = rules.get(result.ruleId) ?? {};
    const message =
      result.message?.text ??
      result.message?.markdown ??
      rule.shortDescription?.text ??
      "CodeQL finding";

    findings.push({
      column: region.startColumn,
      helpUri: rule.helpUri,
      level: result.level ?? "warning",
      line: region.startLine,
      message,
      ruleId: result.ruleId ?? "CodeQL",
      uri,
    });
  }
}

if (findings.length === 0) {
  console.log("No CodeQL findings.");
  process.exit(0);
}

console.error(`CodeQL found ${findings.length} finding(s):`);

for (const finding of findings) {
  const location = [
    finding.uri,
    finding.line ? `:${finding.line}` : "",
    finding.column ? `:${finding.column}` : "",
  ].join("");
  const help = finding.helpUri ? ` (${finding.helpUri})` : "";
  const summaryPrefix = `- [${finding.level}] ${finding.ruleId} ${location} - `;
  const summary = `${summaryPrefix}${finding.message}${help}`;
  console.error(summary);
  const annotationProperties = {
    col: finding.column,
    file: finding.uri,
    line: finding.line,
    title: `CodeQL ${finding.ruleId}`,
  };
  const propertyText = annotationPropertiesText(annotationProperties);
  const escapedMessage = escapeMessage(finding.message);
  console.error(`::error ${propertyText}::${escapedMessage}`);
}

process.exit(1);

function isAcceptedSuppression(result) {
  const suppressions = result.suppressions ?? [];
  return suppressions.some((suppression) => suppression.status === "accepted");
}

function annotationPropertiesText(properties) {
  const propertyText = Object.entries(properties)
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => `${key}=${escapeProperty(value)}`)
    .join(",");

  return propertyText;
}

function escapeMessage(value) {
  let text = String(value);
  text = text.replaceAll("%", "%25");
  text = text.replaceAll("\r", "%0D");
  text = text.replaceAll("\n", "%0A");
  return text;
}

function escapeProperty(value) {
  return escapeMessage(value).replaceAll(":", "%3A").replaceAll(",", "%2C");
}
