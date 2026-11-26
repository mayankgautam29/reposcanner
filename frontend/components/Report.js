import AgentLog from "./AgentLog";
import AiReview from "./AiReview";
import RepoFacts from "./RepoFacts";
import RuleFindings from "./RuleFindings";
import Suggestions from "./Suggestions";
import Verdict from "./Verdict";

export default function Report({ report }) {
  return (
    <div>
      <Verdict report={report} />
      <RepoFacts report={report} />
      <RuleFindings report={report} />
      <AiReview report={report} />
      <Suggestions suggestions={report.suggestions} />
      <AgentLog log={report.log} />
    </div>
  );
}
