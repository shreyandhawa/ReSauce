from resauce import __version__
from resauce.__main__ import main


def test_main_reports_name_and_version(capsys):
    exit_code = main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ReSauce" in output
    assert __version__ in output
