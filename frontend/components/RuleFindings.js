import Health from "./Health";
import Penalties from "./Penalties";
import Quality from "./Quality";
import Secrets from "./Secrets";
import Section from "./Section";
import SubHeading from "./SubHeading";

export default function RuleFindings({ report }) {
  const rules = report.rules;

  return (
    <Section number="02" title="Rule findings" note="Plain if-then rules and regular expressions. No AI here." delay={150}>
      <SubHeading>Points lost</SubHeading>
      <Penalties rules={rules} />

      <SubHeading>Secret finder</SubHeading>
      <Secrets secrets={rules.secrets} />

      <SubHeading>Project health</SubHeading>
      <Health health={rules.health} />

      <SubHeading>Code quality</SubHeading>
      <Quality quality={rules.quality} />
    </Section>
  );
}
