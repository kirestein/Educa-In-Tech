import json
from datetime import datetime
from decimal import Decimal

import gspread
from django.conf import settings


class GoogleSheetsConfigError(Exception):
    """Raised when Google Sheets integration is not configured correctly."""


class GoogleSheetsSyncError(Exception):
    """Raised when data sync with Google Sheets fails."""


def _to_text(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    return value


def _build_row(turma, dashboard_data: dict, dias: int | None):
    comparativo = dashboard_data.get('comparativo_turma') or {}
    return [
        datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        turma.id,
        turma.nome,
        turma.disciplina.nome,
        turma.unidade.nome,
        turma.ano_letivo,
        dias,
        _to_text(dashboard_data.get('media_geral')),
        dashboard_data.get('total_alunos'),
        dashboard_data.get('total_avaliacoes'),
        dashboard_data.get('total_notas_lancadas'),
        _to_text(dashboard_data.get('percentual_notas_lancadas')),
        comparativo.get('posicao'),
        comparativo.get('total_turmas'),
        _to_text(comparativo.get('media_turma')),
        _to_text(comparativo.get('media_coorte')),
        _to_text(comparativo.get('diferenca_media')),
        json.dumps(dashboard_data.get('distribuicao_notas') or {}, ensure_ascii=False),
        json.dumps(dashboard_data.get('media_por_tipo_avaliacao') or [], ensure_ascii=False),
        json.dumps(dashboard_data.get('serie_avaliacoes') or [], ensure_ascii=False),
        json.dumps(dashboard_data.get('recorte_periodo'), ensure_ascii=False),
    ]


def export_dashboard_to_google_sheets(
    *, turma, dashboard_data: dict, dias: int | None, spreadsheet_id: str | None, worksheet_name: str | None
):
    credentials_file = settings.GOOGLE_SHEETS_CREDENTIALS_FILE
    target_spreadsheet_id = spreadsheet_id or settings.GOOGLE_SHEETS_DEFAULT_SPREADSHEET_ID
    target_worksheet_name = worksheet_name or settings.GOOGLE_SHEETS_DEFAULT_WORKSHEET

    if not credentials_file:
        raise GoogleSheetsConfigError('GOOGLE_SHEETS_CREDENTIALS_FILE não configurado.')
    if not target_spreadsheet_id:
        raise GoogleSheetsConfigError('Spreadsheet de destino não configurado.')

    try:
        client = gspread.service_account(filename=credentials_file)
        spreadsheet = client.open_by_key(target_spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(target_worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=target_worksheet_name, rows=1000, cols=24)
            worksheet.append_row(
                [
                    'exported_at',
                    'turma_id',
                    'turma_nome',
                    'disciplina',
                    'unidade',
                    'ano_letivo',
                    'dias_recorte',
                    'media_geral',
                    'total_alunos',
                    'total_avaliacoes',
                    'total_notas_lancadas',
                    'percentual_notas_lancadas',
                    'comparativo_posicao',
                    'comparativo_total_turmas',
                    'comparativo_media_turma',
                    'comparativo_media_coorte',
                    'comparativo_diferenca_media',
                    'distribuicao_notas_json',
                    'media_por_tipo_json',
                    'serie_avaliacoes_json',
                    'recorte_periodo_json',
                ]
            )

        row = _build_row(turma=turma, dashboard_data=dashboard_data, dias=dias)
        worksheet.append_row(row, value_input_option='RAW')
        return {
            'spreadsheet_id': target_spreadsheet_id,
            'worksheet': target_worksheet_name,
            'linhas_enviadas': 1,
        }
    except GoogleSheetsConfigError:
        raise
    except Exception as exc:
        raise GoogleSheetsSyncError('Falha ao exportar dados para Google Sheets.') from exc
