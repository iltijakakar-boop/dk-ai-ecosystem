from typing import Any, Dict, Optional

from app.core.logging import logger


class RulesEngine:
    """
    Evaluates conditional IF-THEN-ELSE automation rules based on variables and operators.
    """

    def evaluate_condition(
        self, condition: Dict[str, Any], variables: Dict[str, Any]
    ) -> bool:
        """
        Recursively evaluates a condition block.
        Conditions can contain:
        - "and": list of conditions
        - "or": list of conditions
        - "not": nested condition
        - "variable", "operator", "value"
        """
        if "and" in condition:
            return all(self.evaluate_condition(c, variables) for c in condition["and"])
        if "or" in condition:
            return any(self.evaluate_condition(c, variables) for c in condition["or"])
        if "not" in condition:
            return not self.evaluate_condition(condition["not"], variables)

        var_name = condition.get("variable")
        operator = condition.get("operator")
        target_value = condition.get("value")

        if not var_name or not operator:
            # Empty or invalid condition is considered True/Passed by default
            return True

        # Fetch variable value from dictionary
        actual_value = variables.get(var_name)

        try:
            if operator == "==":
                return actual_value == target_value
            elif operator == "!=":
                return actual_value != target_value
            elif operator == ">":
                return actual_value > target_value
            elif operator == "<":
                return actual_value < target_value
            elif operator == ">=":
                return actual_value >= target_value
            elif operator == "<=":
                return actual_value <= target_value
            elif operator == "contains":
                return target_value in actual_value if actual_value else False
            elif operator == "in":
                return actual_value in target_value if target_value else False
            else:
                logger.error(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(
                f"Error evaluating condition ({var_name} {operator} {target_value}): {e}"
            )
            return False

    def evaluate_rule(
        self, rule_definition: Dict[str, Any], variables: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates a rule definition dictionary structured as:
        {
          "if": { ...condition... },
          "then": { ...action details... },
          "else": { ...action details... }
        }
        Returns the action dict ("then" or "else") depending on condition outcomes.
        """
        if "if" not in rule_definition:
            # If no condition is set, run then action by default
            return rule_definition.get("then")

        condition = rule_definition["if"]
        passed = self.evaluate_condition(condition, variables)

        if passed:
            logger.info("Automation rule condition PASSED. Executing 'then' branch.")
            return rule_definition.get("then")
        else:
            logger.info("Automation rule condition FAILED. Executing 'else' branch.")
            return rule_definition.get("else")


rules_engine = RulesEngine()
