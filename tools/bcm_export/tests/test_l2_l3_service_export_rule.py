import unittest

from tools.bcm_export.domain_model import BCMModel, CapabilityL1, CapabilityL2
from tools.bcm_export.normalizer import BCMNormalizer


class TestL2L3ServiceExportRule(unittest.TestCase):
    def test_l2_with_l3_children_is_not_exported_as_service(self):
        model = BCMModel(
            capabilities_l1=[
                CapabilityL1(
                    id="CAP.COEUR.005",
                    name="Sinistres",
                    description="Domaine sinistres",
                    owner="Gestion Sinistres",
                    zoning="SERVICES_COEUR",
                )
            ],
            capabilities_l2=[
                CapabilityL2(
                    id="CAP.COEUR.005.IND",
                    name="Instruction du dossier",
                    description="Capacité L2 parent",
                    owner="Gestion Sinistres",
                    parent_l1_id="CAP.COEUR.005",
                    zoning="SERVICES_COEUR",
                    level="L2",
                ),
                CapabilityL2(
                    id="CAP.COEUR.005.IND.COV",
                    name="Instruction couverture",
                    description="Capacité L3 enfant",
                    owner="Gestion Sinistres",
                    parent_l1_id="CAP.COEUR.005",
                    parent_l2_id="CAP.COEUR.005.IND",
                    zoning="SERVICES_COEUR",
                    level="L3",
                ),
                CapabilityL2(
                    id="CAP.COEUR.005.DSP",
                    name="Déclaration",
                    description="Capacité L2 sans enfant",
                    owner="Gestion Sinistres",
                    parent_l1_id="CAP.COEUR.005",
                    zoning="SERVICES_COEUR",
                    level="L2",
                ),
            ],
        )

        normalized = BCMNormalizer().normalize_model(model)

        exported_service_source_ids = {
            service["metadata"]["bcm"]["source_id"]
            for service in normalized["services"]
        }

        self.assertNotIn("CAP.COEUR.005.IND", exported_service_source_ids)
        self.assertIn("CAP.COEUR.005.IND.COV", exported_service_source_ids)
        self.assertIn("CAP.COEUR.005.DSP", exported_service_source_ids)

        excluded = normalized["metadata"].get("excluded_services_due_to_l3", [])
        self.assertEqual(excluded, ["CAP.COEUR.005.IND"])


if __name__ == "__main__":
    unittest.main()
