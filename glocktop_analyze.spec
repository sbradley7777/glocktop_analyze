%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: A tool that analyzes files outputted by glocktop.
Name: glocktop_analyze
Version: 0.1
Release: 3%{?dist}
URL: https://github.com/sbradley7777/glocktop_analyze
Source0: %{name}-%{version}.tar.gz
License: GPLv3
Group: Applications/Archiving
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
BuildRequires: python-devel >= 2.6.5 python-setuptools
Requires: python >= 2.6.5

%description
The glocktop_analyze script analyzes the output generated by glocktop. glocktop
is gathers data on a GFS2 filesystem.

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__rm} -rf ${RPM_BUILD_ROOT}
%{__python}  setup.py install --optimize 1 --root=${RPM_BUILD_ROOT}

%clean
%{__rm} -rf ${RPM_BUILD_ROOT}

%files
%defattr(-,root,root,-)
#%doc LICENSE AUTHORS PKG-INFO CHANGELOG
%doc LICENSE
#%doc doc/*
%{_bindir}/glocktop_analyze.py
%{python_sitelib}/*


%changelog
* Thu Feb 11 2016 Shane Bradley <sbradley@redhat.com>- 0.1-3
- First release of glocktop_analyze.
