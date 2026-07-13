{ lib, stdenvNoCC, python3 }:
let
	pythonWithDeps = python3.withPackages (pypkgs: [
		pypkgs.python-dateutil
	]);
in
stdenvNoCC.mkDerivation {
	pname = "arbeitszeit.py";
	version = "v1.1";
	buildInputs = [ pythonWithDeps ];

	dontUnpack = true;
	arbeitszeit_py = ./arbeitszeit.py;
	holidays_at = ./holidays-at;

	installPhase = ''
		install -Dm 755 $arbeitszeit_py $out/bin/arbeitszeit.py
		install -Dm 644 $holidays_at $out/usr/share/arbeitszeit.py/holidays-at
	'';

	meta = {
		description = "Keep track of your working hours using plain text files";
		homepage = "https://github.com/haansn08/arbeitszeit.py";
		license = lib.licenses.gpl3Only;
	};
}
