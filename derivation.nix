{ lib, stdenv, python3 }:
let
	pythonWithDeps = python3.withPackages (pypkgs: [
		pypkgs.python-dateutil
	]);
in
stdenv.mkDerivation {
	pname = "arbeitszeit.py";
	version = "v1.0.1";
	buildInputs = [ pythonWithDeps ];
	meta = {
		description = "Keep track of your working hours the UNIX way - using plain text files";
		homepage = "https://github.com/haansn08/arbeitszeit.py";
		license = lib.licenses.gpl3Only;
	};
		
	src = fetchTarball {
		url = "https://github.com/haansn08/arbeitszeit.py/archive/refs/tags/v1.0.1.tar.gz";
		sha256 = "1a3p05qrmawhkxh8zy68dh4r35qbi4kgmmwd481mpg9n3r9gxgr4";
	};
	
	installPhase = ''
		mkdir -p $out/bin
		install -m 755 $src/arbeitszeit.py $out/bin
	'';
}
