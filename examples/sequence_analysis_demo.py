"""
Sequence Number Analysis Demo

This script demonstrates how to use the MCP sequence analysis prompt
to analyze D365 Finance & Operations sequence numbers.
"""

import asyncio
import os
from typing import Any, Dict, List

from d365fo_client import D365FOClient, FOClientConfig
from d365fo_client.mcp.prompts.sequence_analysis import (
    SequenceAnalysisPrompt,
    SequenceAnalysisPromptArgs,
    SequenceAnalysisType,
    SequenceScope,
)


class SequenceAnalysisDemo:
    """Demo class for sequence number analysis."""

    def __init__(self):
        """Initialize the demo with D365FO client."""
        base_url = os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        )

        config = FOClientConfig(
            base_url=base_url, use_default_credentials=True, use_label_cache=True
        )

        self.client = D365FOClient(config=config)
        self.prompt_handler = SequenceAnalysisPrompt()

    async def analyze_manual_sequences(self) -> Dict[str, Any]:
        """Analyze all manual sequence numbers."""
        print("=== Analyzing Manual Sequence Numbers ===")

        # Get manual sequences data
        query = self.prompt_handler.get_data_retrieval_queries()["manual_sequences"]
        manual_sequences = await self.client.get_data(
            "SequenceV2Tables",
            filter="Manual eq true",
            select="NumberSequenceCode,ScopeType,ScopeValue,Name,NextRec,Format,Company,InUse,Stopped",
        )

        # Get references for manual sequences
        sequence_codes = [
            seq["NumberSequenceCode"] for seq in manual_sequences["value"]
        ]
        references = []

        for code in sequence_codes:
            ref_data = await self.client.get_data(
                "NumberSequencesV2References",
                filter=f"NumberSequenceCode eq '{code}'",
                select="DataTypeName,NumberSequenceCode,AllowUserChanges,Company",
            )
            references.extend(ref_data["value"])

        result = {
            "analysis_type": "Manual Sequences",
            "total_manual_sequences": len(manual_sequences["value"]),
            "sequences": manual_sequences["value"],
            "references": references,
            "insights": self._analyze_manual_sequence_patterns(
                manual_sequences["value"], references
            ),
        }

        self._print_manual_sequence_summary(result)
        return result

    async def analyze_customer_sequences(self) -> Dict[str, Any]:
        """Analyze sequence numbers used by customer-related entities."""
        print("\n=== Analyzing Customer-Related Sequence Numbers ===")

        # Get customer-related sequence references
        customer_refs = await self.client.get_data(
            "NumberSequencesV2References",
            filter="contains(DataTypeName,'Cust')",
            select="DataTypeName,NumberSequenceCode,ScopeType,ScopeValue,Company",
        )

        # Get sequence details for customer sequences
        sequence_codes = list(
            set([ref["NumberSequenceCode"] for ref in customer_refs["value"]])
        )
        sequence_details = []

        for code in sequence_codes:
            seq_data = await self.client.get_data(
                "SequenceV2Tables",
                filter=f"NumberSequenceCode eq '{code}'",
                select="NumberSequenceCode,Name,Format,NextRec,LargestValue,Manual,InUse,Company",
            )
            sequence_details.extend(seq_data["value"])

        result = {
            "analysis_type": "Customer Sequences",
            "total_references": len(customer_refs["value"]),
            "unique_sequences": len(sequence_codes),
            "references": customer_refs["value"],
            "sequence_details": sequence_details,
            "insights": self._analyze_customer_sequence_patterns(
                customer_refs["value"], sequence_details
            ),
        }

        self._print_customer_sequence_summary(result)
        return result

    async def analyze_sequence_health(self) -> Dict[str, Any]:
        """Perform comprehensive sequence health analysis."""
        print("\n=== Sequence Health Analysis ===")

        # Get all sequences
        all_sequences = await self.client.get_data(
            "SequenceV2Tables",
            select="NumberSequenceCode,Name,NextRec,LargestValue,SmallestValue,Format,InUse,Stopped,Manual,Company",
        )

        # Get all references
        all_references = await self.client.get_data(
            "NumberSequencesV2References",
            select="DataTypeName,NumberSequenceCode,Company",
        )

        health_analysis = self._perform_health_analysis(
            all_sequences["value"], all_references["value"]
        )

        result = {
            "analysis_type": "Health Check",
            "total_sequences": len(all_sequences["value"]),
            "total_references": len(all_references["value"]),
            "health_metrics": health_analysis,
            "sequences": all_sequences["value"],
            "references": all_references["value"],
        }

        self._print_health_analysis(result)
        return result

    def _analyze_manual_sequence_patterns(
        self, sequences: List[Dict], references: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze patterns in manual sequences."""
        active_manual = [
            s for s in sequences if s.get("InUse") and not s.get("Stopped")
        ]
        stopped_manual = [s for s in sequences if s.get("Stopped")]

        # Group by company
        by_company = {}
        for seq in sequences:
            company = seq.get("Company", "Unknown")
            if company not in by_company:
                by_company[company] = []
            by_company[company].append(seq)

        return {
            "active_count": len(active_manual),
            "stopped_count": len(stopped_manual),
            "companies_affected": len(by_company),
            "by_company": by_company,
            "entities_using_manual": len(set([r["DataTypeName"] for r in references])),
            "recommendations": [
                "Review manual sequences for proper access controls",
                "Consider automation for high-volume manual sequences",
                "Implement monitoring for manual sequence gaps",
            ],
        }

    def _analyze_customer_sequence_patterns(
        self, references: List[Dict], sequences: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze patterns in customer-related sequences."""
        entities = set([r["DataTypeName"] for r in references])
        companies = set([r.get("Company", "Unknown") for r in references])

        # Check for manual customer sequences
        manual_sequences = [s for s in sequences if s.get("Manual")]

        return {
            "customer_entities": list(entities),
            "companies_with_customer_sequences": list(companies),
            "manual_customer_sequences": len(manual_sequences),
            "total_customer_entities": len(entities),
            "recommendations": [
                "Ensure customer account numbering is consistent across companies",
                "Review format patterns for customer sequences",
                "Consider preallocation for high-volume customer creation",
            ],
        }

    def _perform_health_analysis(
        self, sequences: List[Dict], references: List[Dict]
    ) -> Dict[str, Any]:
        """Perform comprehensive health analysis."""
        # Near limit sequences (>80% utilized)
        near_limit = []
        for seq in sequences:
            next_rec = seq.get("NextRec", 0)
            largest = seq.get("LargestValue", 0)
            if largest > 0 and next_rec > 0:
                utilization = (next_rec / largest) * 100
                if utilization > 80:
                    near_limit.append(
                        {**seq, "utilization_percent": round(utilization, 2)}
                    )

        # Stopped sequences
        stopped = [s for s in sequences if s.get("Stopped")]

        # Unused sequences (no references)
        referenced_codes = set([r["NumberSequenceCode"] for r in references])
        unused = [
            s for s in sequences if s["NumberSequenceCode"] not in referenced_codes
        ]

        # Orphaned references (no sequence definition)
        sequence_codes = set([s["NumberSequenceCode"] for s in sequences])
        orphaned_refs = [
            r for r in references if r["NumberSequenceCode"] not in sequence_codes
        ]

        return {
            "near_limit_sequences": near_limit,
            "stopped_sequences": stopped,
            "unused_sequences": unused,
            "orphaned_references": orphaned_refs,
            "health_score": self._calculate_health_score(
                len(sequences),
                len(near_limit),
                len(stopped),
                len(unused),
                len(orphaned_refs),
            ),
        }

    def _calculate_health_score(
        self, total: int, near_limit: int, stopped: int, unused: int, orphaned: int
    ) -> int:
        """Calculate overall health score (0-100)."""
        if total == 0:
            return 100

        issues = near_limit + stopped + unused + orphaned
        score = max(0, 100 - (issues / total * 100))
        return round(score)

    def _print_manual_sequence_summary(self, result: Dict[str, Any]):
        """Print summary of manual sequence analysis."""
        print(f"Total Manual Sequences: {result['total_manual_sequences']}")
        print(f"Active Manual Sequences: {result['insights']['active_count']}")
        print(f"Stopped Manual Sequences: {result['insights']['stopped_count']}")
        print(f"Companies Affected: {result['insights']['companies_affected']}")
        print(
            f"Entities Using Manual Sequences: {result['insights']['entities_using_manual']}"
        )

        print("\nTop Manual Sequences:")
        for seq in result["sequences"][:5]:
            status = (
                "🟢 Active"
                if seq.get("InUse") and not seq.get("Stopped")
                else "🔴 Inactive"
            )
            print(
                f"  {seq['NumberSequenceCode']} ({seq.get('Company', 'N/A')}) - {seq.get('Name', 'N/A')} - {status}"
            )

    def _print_customer_sequence_summary(self, result: Dict[str, Any]):
        """Print summary of customer sequence analysis."""
        print(f"Total Customer Entity References: {result['total_references']}")
        print(f"Unique Customer Sequences: {result['unique_sequences']}")
        print(f"Customer Entity Types: {result['insights']['total_customer_entities']}")
        print(
            f"Manual Customer Sequences: {result['insights']['manual_customer_sequences']}"
        )

        print("\nCustomer Entity Types:")
        for entity in result["insights"]["customer_entities"][:10]:
            print(f"  📋 {entity}")

    def _print_health_analysis(self, result: Dict[str, Any]):
        """Print health analysis summary."""
        health = result["health_metrics"]
        score = health["health_score"]

        print(
            f"Overall Health Score: {score}/100 {'🟢' if score >= 80 else '🟡' if score >= 60 else '🔴'}"
        )
        print(f"Total Sequences: {result['total_sequences']}")
        print(f"Near Limit (>80%): {len(health['near_limit_sequences'])}")
        print(f"Stopped Sequences: {len(health['stopped_sequences'])}")
        print(f"Unused Sequences: {len(health['unused_sequences'])}")
        print(f"Orphaned References: {len(health['orphaned_references'])}")

        if health["near_limit_sequences"]:
            print("\n⚠️  Sequences Near Limit:")
            for seq in health["near_limit_sequences"][:5]:
                print(
                    f"  {seq['NumberSequenceCode']} ({seq.get('Company', 'N/A')}) - {seq['utilization_percent']}% utilized"
                )

        if health["stopped_sequences"]:
            print("\n🛑 Stopped Sequences:")
            for seq in health["stopped_sequences"][:5]:
                print(
                    f"  {seq['NumberSequenceCode']} ({seq.get('Company', 'N/A')}) - {seq.get('Name', 'N/A')}"
                )

    async def run_comprehensive_demo(self):
        """Run comprehensive sequence analysis demo."""
        try:
            print("🚀 Starting D365FO Sequence Number Analysis Demo")
            print("=" * 60)

            # Test connection
            version = await self.client.get_application_version()
            print(
                f"Connected to D365FO: {version.get('ApplicationVersion', 'Unknown')}"
            )

            # Run different types of analysis
            manual_result = await self.analyze_manual_sequences()
            customer_result = await self.analyze_customer_sequences()
            health_result = await self.analyze_sequence_health()

            print("\n" + "=" * 60)
            print("📊 Analysis Complete!")
            print(
                f"Manual Sequences Analyzed: {manual_result['total_manual_sequences']}"
            )
            print(f"Customer Sequences Analyzed: {customer_result['unique_sequences']}")
            print(
                f"Overall Health Score: {health_result['health_metrics']['health_score']}/100"
            )

            return {
                "manual_analysis": manual_result,
                "customer_analysis": customer_result,
                "health_analysis": health_result,
            }

        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
            raise
        finally:
            await self.client.close()


async def main():
    """Main demo function."""
    demo = SequenceAnalysisDemo()

    try:
        # Run comprehensive demo
        results = await demo.run_comprehensive_demo()

        # Show prompt template usage
        print("\n" + "=" * 60)
        print("📝 MCP Prompt Template Example")
        print("=" * 60)

        prompt_args = SequenceAnalysisPromptArgs(
            analysis_type=SequenceAnalysisType.COMPREHENSIVE,
            scope=SequenceScope.ALL,
            include_metadata=True,
            include_usage_stats=True,
            include_recommendations=True,
        )

        template = SequenceAnalysisPrompt.get_prompt_template()
        print("Prompt template ready for MCP server usage.")
        print(
            "Use this template with AI assistants for comprehensive sequence analysis."
        )

        # Show available queries
        print("\n📋 Available OData Queries:")
        queries = SequenceAnalysisPrompt.get_data_retrieval_queries()
        for name, query in queries.items():
            print(f"  {name}: {query.strip()[:100]}...")

    except Exception as e:
        print(f"Demo failed: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    # Run the demo
    exit_code = asyncio.run(main())
    exit(exit_code)
