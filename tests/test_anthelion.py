#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pruebas de validación del módulo Anthelion para OLLIN V30.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../modules/anthelion')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ollin_anthelion_v28 import AnthelionKernel, ejecutar_aho_anthelion


class TestAnthelionKernel:
    """Pruebas del kernel de cálculo de Anthelion."""

    def test_calcular_punto_antisolar_correcto(self):
        """Verifica que el punto antisolar se calcule correctamente."""
        kernel = AnthelionKernel()
        pos, msg = kernel.calcular_punto_antisolar(45.0, 20.0)

        assert pos == (225.0, 20.0)
        assert "SIMETRÍA VALIDADA" in msg

    def test_calcular_punto_antisolar_limites(self):
        """Verifica el cálculo cerca del límite 360°."""
        kernel = AnthelionKernel()
        pos, msg = kernel.calcular_punto_antisolar(350.0, 10.0)

        assert pos == (170.0, 10.0)
        assert "SIMETRÍA VALIDADA" in msg

    def test_filtro_parry_visible(self):
        """Verifica que cristales bien orientados den visibilidad 1.0."""
        kernel = AnthelionKernel()
        visibilidad = kernel.filtro_cristales_parry(0.0)
        assert visibilidad == 1.0

        visibilidad = kernel.filtro_cristales_parry(0.5)
        assert visibilidad == 1.0

    def test_filtro_parry_no_visible(self):
        """Verifica que cristales mal orientados den visibilidad 0.0."""
        kernel = AnthelionKernel()
        visibilidad = kernel.filtro_cristales_parry(0.6)
        assert visibilidad == 0.0

        visibilidad = kernel.filtro_cristales_parry(10.0)
        assert visibilidad == 0.0

    def test_generar_metadatos(self):
        """Verifica que los metadatos contengan los campos requeridos."""
        kernel = AnthelionKernel()
        meta = kernel.generar_metadatos_respaldo("test_input", "test_result")

        campos_requeridos = ["obra", "modulo", "protocolo", "timestamp", "signature_sha256", "status"]
        for campo in campos_requeridos:
            assert campo in meta

        assert meta["modulo"] == "C-AHO_Anthelion"
        assert meta["protocolo"] == "v28_Molecular"
        assert meta["status"] == "POWERED BY OLLIN"


class TestEjecucionAnthelion:
    """Pruebas de ejecución completa del módulo."""

    def test_ejecucion_correcta(self):
        """Verifica que la ejecución completa funcione con datos válidos."""
        resultado = ejecutar_aho_anthelion(45.0, 20.0, 0.1)

        assert "coordenadas_anthelion" in resultado
        assert "probabilidad_visibilidad" in resultado
        assert "metadatos" in resultado
        assert resultado["probabilidad_visibilidad"] == 1.0

    def test_ejecucion_con_visibilidad_nula(self):
        """Verifica que cristales mal orientados den visibilidad 0."""
        resultado = ejecutar_aho_anthelion(45.0, 20.0, 10.0)

        assert resultado["probabilidad_visibilidad"] == 0.0
        assert resultado["coordenadas_anthelion"] == (225.0, 20.0)

    def test_ejecucion_con_asimetria(self):
        """Este test es conceptual: el kernel actual no valida entrada asimétrica."""
        # Nota: En la implementación actual, calcular_punto_antisolar siempre
        # retorna SIMETRÍA VALIDADA porque la operación es matemática.
        # Para futuras versiones: validar que az y el estén en rangos correctos.
        pass
