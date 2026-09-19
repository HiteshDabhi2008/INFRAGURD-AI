import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, User as UserIcon, Mail, Phone, Building2, 
  MapPin, Lock, Save, KeyRound, Search, CheckCircle2, 
  AlertTriangle, Users, History, X, Edit2
} from 'lucide-react';
import { authApi, adminApi } from '../../services/api';
import type { UserProfile as UserProfileType, AdminUserItem, AuditLogItem } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

export const UserProfile: React.FC = () => {
  const { user: authUser } = useAuth();
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [loading, setLoading] = useState(true);

  // Profile Edit State
  const [isEditing, setIsEditing] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null);
  const [profileErrorMsg, setProfileErrorMsg] = useState<string | null>(null);

  const [fullName, setFullName] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [designation, setDesignation] = useState('');
  const [organization, setOrganization] = useState('');
  const [department, setDepartment] = useState('');
  const [agency, setAgency] = useState('');
  const [stateRegion, setStateRegion] = useState('');

  // Password Change State
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [pwSuccessMsg, setPwSuccessMsg] = useState<string | null>(null);
  const [pwErrorMsg, setPwErrorMsg] = useState<string | null>(null);

  // Super Admin Management State
  const isSuperAdmin = profile?.canonical_role === 'SUPER_ADMIN' || 
                       profile?.authority_type === 'Super Admin' ||
                       authUser?.authority_type === 'Super Admin';

  const [adminUsers, setAdminUsers] = useState<AdminUserItem[]>([]);
  const [adminSearch, setAdminSearch] = useState('');
  const [adminRoleFilter, setAdminRoleFilter] = useState('All');
  const [loadingUsers, setLoadingUsers] = useState(false);

  const [editingUser, setEditingUser] = useState<AdminUserItem | null>(null);
  const [savingUserEdit, setSavingUserEdit] = useState(false);

  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'admin_users' | 'audit_logs'>('profile');

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    if (isSuperAdmin && activeTab === 'admin_users') {
      fetchAdminUsers();
    } else if (isSuperAdmin && activeTab === 'audit_logs') {
      fetchAuditLogs();
    }
  }, [isSuperAdmin, activeTab]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await authApi.getMe();
      setProfile(res.data);
      populateForm(res.data);
    } catch (err) {
      console.error('Failed to fetch profile', err);
    } finally {
      setLoading(false);
    }
  };

  const populateForm = (data: UserProfileType) => {
    setFullName(data.full_name || '');
    setMobileNumber(data.mobile_number || '');
    setDesignation(data.designation || '');
    setOrganization(data.organization || '');
    setDepartment(data.department || '');
    setAgency(data.agency || '');
    setStateRegion(data.state_region || '');
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileSuccessMsg(null);
    setProfileErrorMsg(null);
    try {
      const res = await authApi.updateProfile({
        full_name: fullName.trim(),
        mobile_number: mobileNumber.trim(),
        designation: designation.trim(),
        organization: organization.trim(),
        department: department.trim(),
        agency: agency.trim(),
        state_region: stateRegion.trim(),
      });
      setProfile(res.data);
      populateForm(res.data);
      setIsEditing(false);
      setProfileSuccessMsg('Profile updated successfully.');
      setTimeout(() => setProfileSuccessMsg(null), 4000);
    } catch (err: any) {
      setProfileErrorMsg(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwSuccessMsg(null);
    setPwErrorMsg(null);
    if (newPassword !== confirmPassword) {
      setPwErrorMsg('New password and confirm password do not match.');
      return;
    }
    if (newPassword.length < 8) {
      setPwErrorMsg('Password must be at least 8 characters long.');
      return;
    }
    setChangingPassword(true);
    try {
      await authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      setPwSuccessMsg('Password changed successfully.');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setPwSuccessMsg(null), 4000);
    } catch (err: any) {
      setPwErrorMsg(err.response?.data?.detail || 'Failed to change password. Verify your old password.');
    } finally {
      setChangingPassword(false);
    }
  };

  const fetchAdminUsers = async () => {
    setLoadingUsers(true);
    try {
      const res = await adminApi.listUsers({
        q: adminSearch || undefined,
        role: adminRoleFilter !== 'All' ? adminRoleFilter : undefined,
      });
      setAdminUsers(res.data);
    } catch (err) {
      console.error('Failed to load admin users', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const fetchAuditLogs = async () => {
    setLoadingLogs(true);
    try {
      const res = await adminApi.listAuditLogs({ limit: 40 });
      setAuditLogs(res.data);
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setLoadingLogs(false);
    }
  };


  const handleToggleUserActive = async (targetUser: AdminUserItem) => {
    try {
      await adminApi.updateUser(targetUser.id, { is_active: !targetUser.is_active });
      fetchAdminUsers();
    } catch (err) {
      alert('Failed to update user status.');
    }
  };

  const handleSaveUserModal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setSavingUserEdit(true);
    try {
      await adminApi.updateUser(editingUser.id, {
        authority_type: editingUser.authority_type,
        is_active: editingUser.is_active,
        is_verified: editingUser.is_verified,
        government_id: editingUser.government_id,
        mobile_number: editingUser.mobile_number,
        department: editingUser.department,
        designation: editingUser.designation,
      });
      setEditingUser(null);
      fetchAdminUsers();
    } catch (err) {
      alert('Failed to save user updates.');
    } finally {
      setSavingUserEdit(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 font-medium">
        <div className="w-8 h-8 border-3 border-government-blue border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading Officer Profile...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <UserIcon className="w-7 h-7 text-government-blue" />
            Official User Profile & Credentials
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Government of India • Ministry of Statistics and Programme Implementation (MoSPI)
          </p>
        </div>

        {isSuperAdmin && (
          <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'profile' ? 'bg-white text-government-blue shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              My Profile
            </button>
            <button
              onClick={() => setActiveTab('admin_users')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'admin_users' ? 'bg-white text-government-blue shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              Manage Users
            </button>
            <button
              onClick={() => setActiveTab('audit_logs')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'audit_logs' ? 'bg-white text-government-blue shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Audit Logs
            </button>
          </div>
        )}
      </div>

      {activeTab === 'profile' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Identity & Security Card */}
          <div className="space-y-6">
            {/* Identity Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="bg-gradient-to-br from-government-blue to-blue-900 p-6 text-white text-center">
                <div className="w-20 h-20 bg-white/20 backdrop-blur-xs rounded-full flex items-center justify-center mx-auto text-white text-2xl font-black border-2 border-white/40 shadow-inner">
                  {profile?.full_name ? profile.full_name.charAt(0).toUpperCase() : 'G'}
                </div>
                <h3 className="text-lg font-bold mt-3">{profile?.full_name}</h3>
                <p className="text-xs text-blue-200 font-medium">{profile?.designation || 'Government Officer'}</p>
                <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 bg-white/10 rounded-full text-xs font-semibold">
                  <ShieldCheck className="w-4 h-4 text-emerald-300" />
                  <span>{profile?.authority_type || 'Authorized Official'}</span>
                </div>
              </div>

              <div className="p-5 space-y-4 text-xs">
                {/* Masked Government ID */}
                <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-blue-700" />
                      Government ID
                    </span>
                    <span className="bg-blue-200 text-blue-900 px-1.5 py-0.5 rounded text-[10px] font-bold">
                      VERIFIED
                    </span>
                  </div>
                  <div className="font-mono text-sm font-black text-blue-950 tracking-wider">
                    {profile?.masked_government_id || 'GOV-****0001'}
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">
                    Government ID is bound to your MoSPI official credential and cannot be altered.
                  </p>
                </div>

                <div className="space-y-2.5 pt-1">
                  <div className="flex items-center gap-2.5 text-slate-600">
                    <Mail className="w-4 h-4 text-slate-400 shrink-0" />
                    <span className="font-medium truncate">{profile?.email}</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-slate-600">
                    <Phone className="w-4 h-4 text-slate-400 shrink-0" />
                    <span>{profile?.mobile_number || 'Mobile not registered'}</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-slate-600">
                    <Building2 className="w-4 h-4 text-slate-400 shrink-0" />
                    <span>{profile?.organization || 'MoSPI / IPMD'}</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-slate-600">
                    <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
                    <span>{profile?.state_region || 'National (All India)'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Change Password Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
                <KeyRound className="w-4 h-4 text-government-blue" />
                Change Official Password
              </h3>

              {pwSuccessMsg && (
                <div className="p-2.5 mb-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{pwSuccessMsg}</span>
                </div>
              )}

              {pwErrorMsg && (
                <div className="p-2.5 mb-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{pwErrorMsg}</span>
                </div>
              )}

              <form onSubmit={handleChangePassword} className="space-y-3">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                    Current Password
                  </label>
                  <input
                    type="password"
                    className="w-full px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-government-blue"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                    New Password (min. 8 chars)
                  </label>
                  <input
                    type="password"
                    className="w-full px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-government-blue"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    className="w-full px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-government-blue"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={changingPassword}
                  className="w-full mt-2 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold transition-colors disabled:bg-slate-300"
                >
                  {changingPassword ? 'Updating Password...' : 'Update Password'}
                </button>
              </form>
            </div>
          </div>

          {/* Right Column: Editable Profile Details */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Official Profile Information</h3>
                  <p className="text-xs text-slate-500">
                    Keep your contact and departmental details up to date for official project notices.
                  </p>
                </div>

                {!isEditing ? (
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="px-3 py-1.5 bg-blue-50 text-government-blue hover:bg-blue-100 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                    Edit Details
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      if (profile) populateForm(profile);
                    }}
                    className="px-3 py-1.5 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-lg text-xs font-semibold transition-colors"
                  >
                    Cancel
                  </button>
                )}
              </div>

              {profileSuccessMsg && (
                <div className="p-3 mb-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{profileSuccessMsg}</span>
                </div>
              )}

              {profileErrorMsg && (
                <div className="p-3 mb-4 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{profileErrorMsg}</span>
                </div>
              )}

              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Full Name */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      disabled={!isEditing}
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                    />
                  </div>

                  {/* Official Email (Read-only) */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1 flex items-center justify-between">
                      <span>Official Email</span>
                      <span className="text-[10px] text-slate-400 font-normal">Fixed</span>
                    </label>
                    <input
                      type="email"
                      disabled
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-100 text-slate-500 cursor-not-allowed"
                      value={profile?.email || ''}
                    />
                  </div>

                  {/* Mobile Number */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Mobile Number
                    </label>
                    <input
                      type="text"
                      disabled={!isEditing}
                      placeholder="+91 98765 43210"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      value={mobileNumber}
                      onChange={(e) => setMobileNumber(e.target.value)}
                    />
                  </div>

                  {/* Designation */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Official Designation
                    </label>
                    <input
                      type="text"
                      disabled={!isEditing}
                      placeholder="e.g. Chief Engineer, Director, Project Officer"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      value={designation}
                      onChange={(e) => setDesignation(e.target.value)}
                    />
                  </div>

                  {/* Organization / Ministry */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Ministry / Organization
                    </label>
                    <input
                      type="text"
                      disabled={!isEditing}
                      placeholder="e.g. Ministry of Road Transport and Highways"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      value={organization}
                      onChange={(e) => setOrganization(e.target.value)}
                    />
                  </div>

                  {/* Department */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Department
                    </label>
                    <input
                      type="text"
                      disabled={!isEditing}
                      placeholder="e.g. Infrastructure Project Monitoring Division"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                    />
                  </div>

                  {/* Agency */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Implementing Agency
                    </label>
                    <input
                      type="text"
                      disabled={!isEditing}
                      placeholder="e.g. NHAI, RVNL, AAI, NTPC"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      value={agency}
                      onChange={(e) => setAgency(e.target.value)}
                    />
                  </div>

                  {/* State / Region */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      State / Territorial Jurisdiction
                    </label>
                    <input
                      type="text"
                      disabled={!isEditing}
                      placeholder="e.g. National, Maharashtra, Gujarat, Delhi"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      value={stateRegion}
                      onChange={(e) => setStateRegion(e.target.value)}
                    />
                  </div>
                </div>

                {isEditing && (
                  <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
                    <button
                      type="button"
                      onClick={() => {
                        setIsEditing(false);
                        if (profile) populateForm(profile);
                      }}
                      className="px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={savingProfile}
                      className="px-6 py-2 bg-government-blue hover:bg-blue-800 text-white rounded-lg text-sm font-semibold shadow-md transition-colors flex items-center gap-2"
                    >
                      <Save className="w-4 h-4" />
                      {savingProfile ? 'Saving Changes...' : 'Save Profile Changes'}
                    </button>
                  </div>
                )}
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Super Admin Users Tab */}
      {isSuperAdmin && activeTab === 'admin_users' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Government Officers & User Accounts</h3>
              <p className="text-xs text-slate-500">
                Search, verify, and manage authority roles across national and state ministries.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search by GovID, Name, or Email..."
                  className="pl-9 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-government-blue w-64"
                  value={adminSearch}
                  onChange={(e) => {
                    setAdminSearch(e.target.value);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') fetchAdminUsers();
                  }}
                />
              </div>

              <select
                className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-slate-50 focus:outline-none"
                value={adminRoleFilter}
                onChange={(e) => {
                  setAdminRoleFilter(e.target.value);
                }}
              >
                <option value="All">All Roles</option>
                <option value="Super Admin">Super Admin</option>
                <option value="MoSPI / IPMD Admin">MoSPI / IPMD Admin</option>
                <option value="Ministry Authority">Ministry Authority</option>
                <option value="Department Authority">Department Authority</option>
                <option value="State Authority">State Authority</option>
                <option value="Agency / Project Authority">Agency / Project Authority</option>
                <option value="Viewer / Auditor">Viewer / Auditor</option>
              </select>

              <button
                onClick={fetchAdminUsers}
                className="px-3 py-1.5 bg-government-blue text-white rounded-lg text-xs font-semibold hover:bg-blue-800 transition-colors"
              >
                Filter
              </button>
            </div>
          </div>

          {loadingUsers ? (
            <div className="py-8 text-center text-xs text-slate-400">Loading user accounts...</div>
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-4">Officer Name & Email</th>
                    <th className="py-3 px-4">Government ID</th>
                    <th className="py-3 px-4">Role / Authority</th>
                    <th className="py-3 px-4">Organization / Dept</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {adminUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">{u.full_name}</div>
                        <div className="text-slate-500 text-[11px]">{u.email}</div>
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-blue-900">
                        {u.masked_government_id || 'Not Assigned'}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800">
                          {u.authority_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        <div>{u.organization || 'MoSPI'}</div>
                        <div className="text-[11px] text-slate-400">{u.department || 'IPMD'}</div>
                      </td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => handleToggleUserActive(u)}
                          className={`px-2 py-0.5 rounded text-[11px] font-bold cursor-pointer transition-colors ${
                            u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {u.is_active ? 'ACTIVE' : 'INACTIVE'}
                        </button>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setEditingUser(u)}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-semibold transition-colors"
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                  {adminUsers.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-slate-400">
                        No user accounts matched the search criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Super Admin Audit Logs Tab */}
      {isSuperAdmin && activeTab === 'audit_logs' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <h3 className="text-base font-bold text-slate-900">System Security & Audit Trail</h3>
              <p className="text-xs text-slate-500">
                Tamper-evident logs of logins, profile updates, role assignments, and monthly project submissions.
              </p>
            </div>
            <button
              onClick={fetchAuditLogs}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
            >
              Refresh
            </button>
          </div>

          {loadingLogs ? (
            <div className="py-8 text-center text-xs text-slate-400">Loading audit trail...</div>
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-2.5 px-4 font-mono text-slate-500 whitespace-nowrap">
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 font-semibold text-slate-800">
                        {log.user_email || 'SYSTEM'}
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-slate-100 text-slate-700">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-600 font-mono text-[11px]">
                        {log.details || '—'}
                      </td>
                    </tr>
                  ))}
                  {auditLogs.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-slate-400">
                        No audit logs recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Edit User Modal for Super Admin */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="bg-slate-900 text-white px-5 py-3.5 flex items-center justify-between">
              <h4 className="text-sm font-bold">Edit Officer Permissions</h4>
              <button onClick={() => setEditingUser(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveUserModal} className="p-5 space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 uppercase mb-1">Officer</label>
                <div className="font-semibold text-slate-900">{editingUser.full_name}</div>
                <div className="text-slate-500">{editingUser.email}</div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 uppercase mb-1">Government ID</label>
                <input
                  type="text"
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-lg bg-slate-50 focus:bg-white"
                  value={editingUser.government_id || ''}
                  onChange={(e) => setEditingUser({ ...editingUser, government_id: e.target.value })}
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 uppercase mb-1">Authority Role</label>
                <select
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-lg bg-slate-50 focus:bg-white"
                  value={editingUser.authority_type}
                  onChange={(e) => setEditingUser({ ...editingUser, authority_type: e.target.value })}
                >
                  <option value="Super Admin">Super Admin</option>
                  <option value="MoSPI / IPMD Admin">MoSPI / IPMD Admin</option>
                  <option value="Ministry Authority">Ministry Authority</option>
                  <option value="Department Authority">Department Authority</option>
                  <option value="State Authority">State Authority</option>
                  <option value="Agency / Project Authority">Agency / Project Authority</option>
                  <option value="Viewer / Auditor">Viewer / Auditor</option>
                </select>
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="font-bold text-slate-700">Account Active</label>
                <input
                  type="checkbox"
                  checked={editingUser.is_active}
                  onChange={(e) => setEditingUser({ ...editingUser, is_active: e.target.checked })}
                  className="w-4 h-4 text-government-blue rounded"
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="font-bold text-slate-700">Government Verified</label>
                <input
                  type="checkbox"
                  checked={editingUser.is_verified}
                  onChange={(e) => setEditingUser({ ...editingUser, is_verified: e.target.checked })}
                  className="w-4 h-4 text-government-blue rounded"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setEditingUser(null)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingUserEdit}
                  className="px-4 py-1.5 bg-government-blue hover:bg-blue-800 text-white rounded-lg font-semibold shadow-xs"
                >
                  {savingUserEdit ? 'Saving...' : 'Save User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfile;
